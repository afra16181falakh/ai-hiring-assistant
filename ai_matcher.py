from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.schemas import CandidateProfile, Education, Experience, JobDescription
from typing import List, Dict
import numpy as np
import re

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
try:
    sentence_transformer_model = SentenceTransformer(model_name)
    EMBEDDING_DIMENSION = sentence_transformer_model.get_sentence_embedding_dimension()
except Exception as e:
    print(f"Error loading SentenceTransformer model '{model_name}': {e}")
    print("Please ensure you have an internet connection or the model is cached.")
    sentence_transformer_model = None
    EMBEDDING_DIMENSION = 384

def generate_text_embedding(text: str) -> List[float]:
    if sentence_transformer_model is None:
        print("Warning: SentenceTransformer model not loaded. Returning zero embedding.")
        return np.zeros(EMBEDDING_DIMENSION).tolist()

    if not text or not isinstance(text, str) or not text.strip():
        return np.zeros(EMBEDDING_DIMENSION).tolist()
    
    return sentence_transformer_model.encode(text, convert_to_tensor=False).tolist()

def create_candidate_embedding_text(profile: CandidateProfile) -> str:
    text_parts = []
    if profile.name:
        text_parts.append(f"Name: {profile.name}.")
    if profile.total_experience_years is not None:
        text_parts.append(f"{profile.total_experience_years} years of experience.")
    if profile.skills:
        text_parts.append(f"Skills: {', '.join(profile.skills)}.")
    
    if profile.education:
        edu_summary = "; ".join([f"{edu.degree} at {edu.institution} ({edu.year})" for edu in profile.education if edu.degree and edu.institution])
        if edu_summary:
            text_parts.append(f"Education: {edu_summary}.")

    if profile.experience:
        exp_summary = "; ".join([f"{exp.title} at {exp.company} ({exp.years})" for exp in profile.experience if exp.title and exp.company])
        if exp_summary:
            text_parts.append(f"Experience: {exp_summary}.")

    return " ".join(filter(None, text_parts)).strip()


def create_job_embedding_text(job: JobDescription) -> str:
    text_parts = []
    if job.title:
        text_parts.append(f"Job Title: {job.title}.")
    if job.description:
        text_parts.append(f"Job Description: {job.description}.")
    
    return " ".join(filter(None, text_parts)).strip()

def get_jd_embedding(jd_text: str) -> List[float]:
    return generate_text_embedding(jd_text)

def generate_explainability(jd_text: str, profile: CandidateProfile) -> Dict:
    explanation = {}
    
    jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
    
    candidate_skills_lower = set([skill.lower() for skill in profile.skills])
    matched_skills = list(jd_words.intersection(candidate_skills_lower))
    if matched_skills:
        explanation["matched_skills"] = sorted(list(set(matched_skills)))

    candidate_raw_words = set(re.findall(r'\b\w+\b', (profile.raw_text or "").lower()))
    common_keywords = list(jd_words.intersection(candidate_raw_words))
    
    unique_common_keywords = [kw for kw in common_keywords if kw not in matched_skills]
    if unique_common_keywords:
        explanation["common_keywords_in_resume"] = sorted(list(set(unique_common_keywords)))[:5]

    if profile.total_experience_years is not None:
        explanation["total_experience"] = f"{profile.total_experience_years} years"
    
    if profile.education:
        edu_summary = "; ".join([f"{edu.degree} at {edu.institution}" for edu in profile.education if edu.degree and edu.institution])
        if edu_summary:
            explanation["education"] = edu_summary

    if profile.experience:
        exp_summary = "; ".join([f"{exp.title} at {exp.company}" for exp in profile.experience if exp.title and exp.company])
        if exp_summary:
            explanation["experience"] = exp_summary

    return explanation

def rank_candidates(job_description_obj: JobDescription, candidates: List[CandidateProfile]) -> List[Dict]:
    if job_description_obj.embedding is None:
        print("Warning: Job description has no pre-computed embedding. Generating on the fly from summary text.")
        jd_summary_text = create_job_embedding_text(job_description_obj)
        jd_embedding_np = np.array(generate_text_embedding(jd_summary_text))
    else:
        jd_embedding_np = np.array(job_description_obj.embedding)

    if not jd_embedding_np.any():
        print("Warning: Job description could not be embedded (likely empty/invalid after processing). Skipping ranking.")
        return []

    ranked_candidates = []

    for profile in candidates:
        if profile.embedding is None:
            print(f"Warning: Candidate {profile.name or profile.id or 'Unknown'} has no pre-computed embedding. Generating on the fly from summary text.")
            candidate_summary_text = create_candidate_embedding_text(profile)
            candidate_embedding_np = np.array(generate_text_embedding(candidate_summary_text))
        else:
            candidate_embedding_np = np.array(profile.embedding)

        if not candidate_embedding_np.any():
            print(f"Warning: Candidate {profile.name or profile.id or 'Unknown'} could not be embedded (likely empty/invalid content). Skipping.")
            continue

        similarity = cosine_similarity(
            jd_embedding_np.reshape(1, -1),
            candidate_embedding_np.reshape(1, -1)
        )[0][0] * 100

        ranked_candidates.append({
            "candidate_profile": profile.model_dump(exclude={"raw_text"}),
            "match_score": round(similarity, 2),
            "explainability": generate_explainability(job_description_obj.description, profile)
        })

    ranked_candidates.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked_candidates