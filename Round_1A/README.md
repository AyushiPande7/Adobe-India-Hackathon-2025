PDF Outline Extractor – Challenge 1A Submission
This project extracts hierarchical outlines (bookmarks) from PDFs and outputs them as structured JSON files. It is containerized using Docker to ensure portability and easy execution.

🔧 Project Structure
graphql
Copy
Edit
.
├── Dockerfile
├── requirements.txt
├── extract_outline.py
├── pdfs/              # Input PDFs folder (user-provided)
└── outputs/           # Output JSON folder (auto-generated)
extract_outline.py: Core script to extract outlines from PDFs.

pdfs/: Place your input .pdf files here before running.

outputs/: This will be populated with .json files after execution.

🐳 How It Works (Behind the Scenes)
We use PyMuPDF (fitz) to access the table of contents from each PDF.

Each outline entry (bookmark) is recursively processed into a nested dictionary structure capturing the title, page number, and child hierarchy.

All processed data is written into clean, human-readable .json files.

The script supports batch processing — every PDF in the /pdfs folder is automatically processed.

✅ Steps to Build and Run
Ensure Docker is installed on your system before proceeding.

1. Build the Docker Image
bash
Copy
Edit
docker build -t pdf-outline-extractor .
This creates a container with all dependencies pre-installed.

2. Prepare Input
Create a pdfs directory in your working folder.

Place all PDFs for outline extraction inside this folder.

3. Run the Container
Windows:
bash
Copy
Edit
docker run --rm -v %cd%/pdfs:/app/pdfs -v %cd%/outputs:/app/outputs pdf-outline-extractor python extract_outline.py --batch pdfs outputs
macOS/Linux:
bash
Copy
Edit
docker run --rm -v "$(pwd)/pdfs":/app/pdfs -v "$(pwd)/outputs":/app/outputs pdf-outline-extractor python extract_outline.py --batch pdfs outputs
📄 Output Format
Each .json output file is named after the original PDF.

Example output structure:

json
Copy
Edit
[
  {
    "title": "Chapter 1",
    "page": 1,
    "children": [
      {
        "title": "Section 1.1",
        "page": 2,
        "children": []
      }
    ]
  }
]