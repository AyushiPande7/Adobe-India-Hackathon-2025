# PDF parsing logic here

import fitz  # PyMuPDF

def extract_sections_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    sections = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if "lines" not in b:
                continue
            for l in b["lines"]:
                line_text = " ".join([span["text"] for span in l["spans"]]).strip()
                if not line_text:
                    continue

                # Treat large or bold fonts as headings
                for span in l["spans"]:
                    font_size = span.get("size", 0)
                    is_bold = "bold" in span.get("font", "").lower()

                    if font_size > 14 or is_bold:
                        sections.append({
                            "section_title": line_text,
                            "content": "",  # We'll update this if needed
                            "page_number": page_num + 1
                        })
                        break
    return sections
