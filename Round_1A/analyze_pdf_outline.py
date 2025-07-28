import os
import sys
import fitz  # PyMuPDF
import json
import re
import logging
import unicodedata
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Sequence

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Try importing optional tokenizer (SentencePiece)
try:
    import sentencepiece as spm
    HAS_SENTENCEPIECE = True
except ImportError:
    HAS_SENTENCEPIECE = False

# Regex patterns for cleanup and filtering
PATTERN_BULLET = re.compile(r"^[\u2022\-\*\d]+\s*")
PATTERN_URL = re.compile(r"^https?://", re.IGNORECASE)
PATTERN_CODE = re.compile(r"^`{3}")

# Font attribute hints
FONT_BOLD_HINTS = ("bold", "black", "heavy", "semibold", "demi")
FONT_ITALIC_HINTS = ("italic", "oblique")

# Title constraints
TEXT_LENGTH_THRESHOLD = 3
TITLE_WORD_LIMIT = 12
EXTENDED_TITLE_THRESHOLD = 25

# Force-level override rules for matching headings
HEADING_OVERRIDES = [
    (re.compile(r"^round\s+1a\b", re.I), "H1"),
    (re.compile(r"^round\s+1b\b", re.I), "H1"),
    (re.compile(r"^appendix$", re.I), "H1"),
]

# Data container for heading metadata
@dataclass
class HeadingEntry:
    type: str
    text: str
    page: int


# --- Utility Functions ---
def is_font_bold(font_name: str) -> bool:
    return any(bold in font_name.lower() for bold in FONT_BOLD_HINTS)

def is_font_italic(font_name: str) -> bool:
    return any(italic in font_name.lower() for italic in FONT_ITALIC_HINTS)

def normalize_text(raw: str) -> str:
    clean = unicodedata.normalize("NFKC", raw)
    return " ".join(clean.split()).strip()

def tokenize_with_sp(text: str, model_path: Optional[str]) -> str:
    if not (model_path and HAS_SENTENCEPIECE and os.path.exists(model_path)):
        return normalize_text(text)
    try:
        sp = spm.SentencePieceProcessor(model_file=model_path)
        encoded = sp.encode(text, out_type=str)
        return " ".join(encoded).strip() or normalize_text(text)
    except Exception:
        return normalize_text(text)

def count_alphanumerics(input_str: str) -> int:
    return sum(char.isalnum() for char in input_str)


# --- Core Extraction Class ---
class PDFHeadingParser:
    def __init__(
        self,
        filepath: str,
        max_pages: int = 50,
        sample_pages: int = 5,
        scan_limit: int = 3,
        tolerance: float = 0.75,
        sp_model_path: Optional[str] = None,
        title_word_cap: int = 12
    ):
        self.filepath = filepath
        self.max_pages = max_pages
        self.sample_pages = sample_pages
        self.scan_limit = scan_limit
        self.tolerance = tolerance
        self.sp_model_path = sp_model_path
        self.title_word_cap = title_word_cap

        self.font_hierarchy: List[float] = []
        self.entries: List[HeadingEntry] = []
        self.inferred_title: Optional[str] = None

    def _tokenize(self, raw: str) -> str:
        return tokenize_with_sp(raw, self.sp_model_path)

    def _determine_font_sizes(self, document: fitz.Document):
        sizes = []
        pages_to_scan = min(document.page_count, self.sample_pages, self.max_pages)

        for idx in range(pages_to_scan):
            try:
                blocks = document[idx].get_text("dict")["blocks"]
            except Exception:
                continue

            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span["text"].strip() and not is_font_italic(span["font"]):
                            sizes.append(span["size"])

        unique_sizes = sorted(set(sizes), reverse=True)
        filtered = []
        for sz in unique_sizes:
            if not filtered or abs(sz - filtered[-1]) > self.tolerance:
                filtered.append(sz)

        self.font_hierarchy = filtered[:3]
        logger.info(f"Top font sizes determined: {self.font_hierarchy}")

    def _map_size_to_level(self, size: float) -> Optional[str]:
        for idx, known in enumerate(self.font_hierarchy):
            if abs(size - known) <= self.tolerance:
                return ("H1", "H2", "H3")[idx]
        return None

    def _qualifies_as_heading(self, content: str, line_count: int = 1) -> bool:
        if line_count > 3:
            return False
        if PATTERN_URL.match(content) or PATTERN_CODE.match(content):
            return False

        sanitized = PATTERN_BULLET.sub("", content).strip()
        if count_alphanumerics(sanitized) < TEXT_LENGTH_THRESHOLD:
            return False

        words = sanitized.split()
        if len(words) > self.title_word_cap and len(words) > EXTENDED_TITLE_THRESHOLD:
            return False
        if sanitized.endswith((".", "?", "!")) and len(words) > 3:
            return False
        return True

    def parse(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            logger.error(f"File not found: {self.filepath}")
            return {"title": "Unknown", "outline": []}

        try:
            document = fitz.open(self.filepath)
        except Exception as open_err:
            logger.error(f"Error reading PDF: {open_err}")
            return {"title": "Unknown", "outline": []}

        if document.page_count == 0:
            document.close()
            return {"title": "Unknown", "outline": []}

        self._determine_font_sizes(document)
        fallback_title = (document.metadata.get("title") or "").strip()
        max_seen_font = -1.0

        for pg_num in range(min(document.page_count, self.max_pages)):
            page = document[pg_num]
            text_data = page.get_text("dict")

            for block in text_data["blocks"]:
                lines = block.get("lines", [])
                flat_spans = [s for l in lines for s in l.get("spans", [])]
                if not flat_spans:
                    continue

                combined_raw = " ".join(span["text"] for span in flat_spans).strip()
                normalized = self._tokenize(combined_raw)
                if not normalized:
                    continue

                all_sizes = sorted([s["size"] for s in flat_spans if s["text"].strip()])
                active_size = all_sizes[len(all_sizes) // 2] if all_sizes else flat_spans[0]["size"]
                font_used = flat_spans[0]["font"]

                heading_level = self._map_size_to_level(active_size)
                if heading_level is None and is_font_bold(font_used) and not is_font_italic(font_used):
                    if self.font_hierarchy and active_size > self.font_hierarchy[-1]:
                        heading_level = "H2"
                    else:
                        heading_level = "H3"

                for regex, level_force in HEADING_OVERRIDES:
                    if regex.search(normalized):
                        heading_level = level_force
                        break

                if PATTERN_BULLET.match(normalized) and len(normalized.split()) > 1:
                    heading_level = "H2" if heading_level == "H1" else "H3" if heading_level == "H2" else heading_level

                if heading_level and self._qualifies_as_heading(normalized, line_count=len(lines)):
                    self.entries.append(HeadingEntry(heading_level, normalized, pg_num + 1))

                if pg_num < self.scan_limit and active_size > max_seen_font:
                    if self._qualifies_as_heading(normalized, line_count=len(lines)):
                        self.inferred_title = normalized
                        max_seen_font = active_size

        document.close()

        if not self.inferred_title:
            self.inferred_title = fallback_title or (self.entries[0].text if self.entries else "Unknown")

        return {
            "title": self.inferred_title,
            "outline": [entry.__dict__ for entry in self.entries]
        }


# --- Batch Processor ---
def process_multiple(input_dir: str, output_dir: str) -> int:
    os.makedirs(output_dir, exist_ok=True)
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    count = 0

    for fname in files:
        full_input = os.path.join(input_dir, fname)
        out_name = os.path.splitext(fname)[0] + ".json"
        full_output = os.path.join(output_dir, out_name)

        parser = PDFHeadingParser(full_input)
        extracted = parser.parse()

        with open(full_output, "w", encoding="utf-8") as outf:
            json.dump(extracted, outf, indent=2, ensure_ascii=False)

        logger.info(f"Exported: {full_output}")
        count += 1

    return count


# --- Helper for Usage ---
def display_usage():
    print("\nExpected usage:")
    print("  python extract_pdf.py <file.pdf> [output.json]")
    print("  python extract_pdf.py --batch <input_folder> <output_folder>")
    sys.exit(1)


# --- Main Execution Path ---
if __name__ == "__main__":
    arguments: Sequence[str] = sys.argv[1:]
    if not arguments:
        display_usage()

    if arguments[0] == "--batch":
        if len(arguments) != 3:
            display_usage()
        total = process_multiple(arguments[1], arguments[2])
        logger.info(f"Finished processing {total} files.")
        sys.exit(0)

    input_pdf = arguments[0]
    output_json = arguments[1] if len(arguments) > 1 else "output/output.json"

    parser = PDFHeadingParser(input_pdf)
    result = parser.parse()

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as out_file:
        json.dump(result, out_file, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))