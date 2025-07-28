# helpers/extract_sections.py

from sentence_transformers import SentenceTransformer, util

# Load the model once (efficient)
model = SentenceTransformer('all-MiniLM-L6-v2')

def rank_sections(sections, persona, job_to_be_done, top_k=5):
    query = f"Persona: {persona}. Task: {job_to_be_done}"
    query_embedding = model.encode(query, convert_to_tensor=True)

    scored_sections = []

    for section in sections:
        text = section["section_title"]
        section_embedding = model.encode(text, convert_to_tensor=True)
        score = util.pytorch_cos_sim(query_embedding, section_embedding).item()

        section["similarity"] = score
        scored_sections.append(section)

    # Sort by descending similarity
    top_sections = sorted(scored_sections, key=lambda x: x["similarity"], reverse=True)[:top_k]

    # Add importance rank
    for idx, s in enumerate(top_sections, 1):
        s["importance_rank"] = idx

    return top_sections
