# main.py

import os
from pathlib import Path
from helpers.json_handler import read_input_json, write_output_json
from helpers.pdf_parser import extract_sections_from_pdf
from helpers.extract_sections import rank_sections
from helpers.subsection_analysis import extract_and_summarize_section

def process_collection(collection_path):
    input_json_path = collection_path / "challenge1b_input.json"
    output_json_path = collection_path / "challenge1b_output.json"

    # Step 1: Load input data
    data = read_input_json(input_json_path)
    persona = data["persona"]["role"]
    job_to_be_done = data["job_to_be_done"]["task"]
    input_docs = [doc["filename"] for doc in data["documents"]]

    all_sections = []

    for doc in input_docs:
        pdf_path = collection_path / "PDFs" / doc
        print(f"\n[+] Extracting from {doc}")
        sections = extract_sections_from_pdf(pdf_path)
        for section in sections:
            section["document"] = doc  # attach source
            all_sections.append(section)

    # Step 2: Rank sections
    ranked_sections = rank_sections(all_sections, persona, job_to_be_done)

    # Step 3: Format extracted_sections
    extracted_sections = [
        {
            "document": s["document"],
            "section_title": s["section_title"],
            "importance_rank": s["importance_rank"],
            "page_number": s["page_number"]
        }
        for s in ranked_sections
    ]

    # Step 4: Subsection analysis (summary from original page)
    subsection_analysis = []
    for section in ranked_sections:
        doc_path = os.path.join(collection_path, "PDFs", section["document"])
        page_number = section["page_number"]
        summary = extract_and_summarize_section(doc_path, page_number)
        if summary:
            subsection_analysis.append({
                "document": section["document"],
                "refined_text": summary,
                "page_number": page_number
            })

    # Step 5: Final output
    output = {
        "input_documents": input_docs,
        "persona": persona,
        "job_to_be_done": job_to_be_done,
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    write_output_json(
        output_json_path,
        output["input_documents"],
        output["persona"],
        output["job_to_be_done"],
        output["extracted_sections"],
        output["subsection_analysis"]
    )

if __name__ == "__main__":
    base_path = Path("D:/PROJECT/trials/Challenge_1b_Solution/collections/Collection_1")
    process_collection(base_path)
