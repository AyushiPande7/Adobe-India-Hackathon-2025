# JSON read/write functions here

# helpers/json_handler.py

import json
from pathlib import Path
from datetime import datetime

def read_input_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def write_output_json(output_path, input_docs, persona, job_to_be_done, extracted_sections, subsection_analysis):
    output = {
        "metadata": {
            "input_documents": input_docs,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.now().isoformat()
        },
        "extracted_sections": extracted_sections,
        "subsection_analysis": subsection_analysis
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"[✓] Output written to {output_path}")
