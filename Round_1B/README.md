# Challenge 1b

# Multi-Collection PDF Analysis - Adobe Hackathon Challenge 1b

This project implements a persona-driven PDF analysis pipeline that processes multiple collections of PDFs, extracts the most relevant sections based on a given job-to-be-done, summarizes them, and outputs structured JSON files.

##  Folder Structure
```bash
Challenge_1b_Solution/
├── collections/
│ ├── Collection_1/
│ │ ├── PDFs/ # Input PDFs
│ │ ├── challenge1b_input.json # Input: persona + task
│ │ └── challenge1b_output.json # Output: extracted and summarized data
│ └── Collection_2/ # Optional
├── helpers/
│ ├── pdf_parser.py # Extracts headings, titles, and page numbers
│ ├── extract_sections.py # Ranks sections using embedding relevance
│ ├── subsection_analysis.py # Extracts + summarizes content from top sections
│ └── utils.py # Common I/O helpers
├── main.py # Entry point to process all collections
```

## ⚙️ How It Works

1. **Input JSON** (`challenge1b_input.json`) contains:
   - List of PDF file names
   - Persona description
   - Job to be done (task)

2. **Pipeline stages**:
   -  Parse all PDFs to extract section titles and page numbers
   -  Rank sections by relevance using sentence-transformers
   -  Extract text from top-ranked pages and summarize
   -  Output a structured JSON with metadata, extracted sections, and summaries

##  Run the Pipeline

Ensure you have all dependencies installed (see below), then run:


python main.py
This processes all collections inside the collections/ folder and writes output JSON files to each one.

 ### Dependencies
 ```bash
Python 3.8+

PyMuPDF (fitz)

Sentence-Transformers (sentence-transformers)

Transformers (transformers)

Torch (torch)

```

Install via:
```bash

pip install -r requirements.txt
```
###  Output Format (challenge1b_output.json)
```bash
{
  "metadata": {
    "input_documents": [...],
    "persona": "...",
    "job_to_be_done": "..."
  },
  "extracted_sections": [
    {
      "document": "...pdf",
      "section_title": "...",
      "page_number": 4,
      "score": 0.87
    }
  ],
  "subsection_analysis": [
    {
      "document": "...pdf",
      "refined_text": "...",
      "page_number": 4
    }
  ]
}
```
