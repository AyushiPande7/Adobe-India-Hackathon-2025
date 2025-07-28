# helpers/subsection_analysis.py

import fitz  # PyMuPDF
from transformers import pipeline

# Load summarization pipeline (efficient + pretrained)
summarizer = pipeline("summarization", model="philschmid/bart-large-cnn-samsum")

def extract_and_summarize_section(pdf_path, page_number):
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number)
        text = page.get_text()

        # Clean and limit length for summarizer (BART has a 1024-token limit)
        cleaned_text = " ".join(text.strip().split())
        cleaned_text = cleaned_text[:3000]  # safe cap to avoid truncation

        # Summarize
        summary = summarizer(cleaned_text, max_length=300, min_length=50, do_sample=False)[0]['summary_text']
        return summary

    except Exception as e:
        print(f"[ERROR] Failed processing page {page_number} of {pdf_path}: {e}")
        return ""
