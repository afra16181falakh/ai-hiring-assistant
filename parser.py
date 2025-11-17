import os
import re
import spacy
import fitz
from app.schemas import CandidateProfile, Education, Experience
from typing import List, Dict, Optional
from datetime import datetime, timezone
from app.ai_matcher import generate_text_embedding, create_candidate_embedding_text

try:
    nlp = spacy.load('en_core_web_sm')
except Exception as e:
    print(f"Error loading spaCy model 'en_core_web_sm': {e}")
    print("Please ensure you have run 'python -m spacy download en_core_web_sm' in your activated venv.")
    nlp = None

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
    return text

def clean_text(text: str) -> str:
    text = re.sub(r'[\r\n]+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    return text

def parse_years_from_date_string(date_string: str) -> List[int]:
    if not date_string:
        return []
    
    current_year = datetime.now().year
    date_string = date_string.lower().replace('present', str(current_year)).strip()

    years = []
    matches = re.findall(r'\b(\d{4})\b', date_string)
    
    if len(matches) >= 2:
        try:
            start_year = int(matches[0])
            end_year = int(matches[-1])
            years = [start_year, end_year]
        except ValueError:
            pass
    elif len(matches) == 1:
        try:
            years = [int(matches[0])]
        except ValueError:
            pass
    
    return years

def extract_education(full_text: str) -> List[Education]:
    education_list: List[Education] = []
    print("\n--- Starting Education Extraction ---")

    education_section_pattern = re.compile(
        r'(?:EDUCATION|ACADEMIC BACKGROUND|DEGREES|QUALIFICATIONS)\n*(.*?)(?=\n(?:SKILLS|EXPERIENCE|WORK HISTORY|PROJECTS|AWARDS|SUMMARY|ABOUT ME|LANGUAGES|PUBLICATIONS|INTERESTS|$))',
        re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    education_section_match = education_section_pattern.search(full_text)
    
    if education_section_match:
        education_content = education_section_match.group(1).strip()
        print(f"Education Section Content (first 500 chars):\n{education_content[:500]}...\n")

        edu_item_pattern = re.compile(
            r'('
                r'(?:(ph\.?d|master(?:\'?s)?|bachelor(?:\'?s)?|mba|m\.?s|b\.?s|associate(?:\'?s)?)\s+(?:of\s+)?[\w\s&,./-]+?)?'
                r'(?:[\s,\-]*at[\s,\-]+|[\s,\-]+)?([\w\s&,./-]+\s*(?:University|College|Institute|School|Academy|Conservatory))'
                r'(?:[\s,\-]+(\d{4}(?:\s*[\-–]?\s*(?:\d{4}|Present|Current))?))?'
            r')|'
            r'(?:'
                r'([\w\s&,./-]+\s*(?:University|College|Institute|School|Academy|Conservatory))'
                r'(?:[\s,\-]+(?:(?:(ph\.?d|master(?:\'?s)?|bachelor(?:\'?s)?|mba|m\.?s|b\.?s|associate(?:\'?s)?)\s+(?:of\s+)?[\w\s&,./-]+?))?)?'
                r'(?:[\s,\-]+(\d{4}(?:\s*[\-–]?\s*(?:\d{4}|Present|Current))?))?'
            r')',
            re.IGNORECASE | re.DOTALL
        )
        
        entries = re.split(
            r'\n(?=\s*(?:[A-Z][a-z]+\s+(?:University|College|Institute|School)|(?:ph\.?d|master|bachelor|mba|m\.?s|b\.?s|associate)\b))',
            education_content,
            flags=re.IGNORECASE | re.MULTILINE
        )
        entries = [entry.strip() for entry in entries if entry.strip()]
        
        if not entries and education_content:
            entries = [education_content]

        for entry in entries:
            match = edu_item_pattern.search(entry)
            if match:
                degree = match.group(2) or match.group(6)
                institution = match.group(3) or match.group(5)
                year = match.group(4) or match.group(7)

                if degree or institution:
                    edu_entry = Education(
                        degree=degree.strip() if degree else None,
                        institution=institution.strip() if institution else None,
                        year=year.strip() if year else None
                    )
                    education_list.append(edu_entry)
                    print(f"  Found Education: {edu_entry.model_dump_json()}")
            else:
                print(f"  No Edu Pattern Match for entry:\n---\n{entry[:200]}...\n---\n")
    else:
        print("  No Education section header found.")
    
    print(f"--- Finished Education Extraction. Found {len(education_list)} entries. ---")
    return education_list

def extract_experience(full_text: str) -> List[Experience]:
    experience_list: List[Experience] = []
    print("\n--- Starting Experience Extraction ---")

    experience_section_pattern = re.compile(
        r'(?:EXPERIENCE|WORK HISTORY|PROFESSIONAL EXPERIENCE|EMPLOYMENT)\n*(.*?)(?=\n(?:EDUCATION|SKILLS|PROJECTS|AWARDS|CERTIFICATIONS|SUMMARY|ABOUT ME|LANGUAGES|PUBLICATIONS|INTERESTS|$))',
        re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    experience_section_match = experience_section_pattern.search(full_text)

    if experience_section_match:
        experience_content = experience_section_match.group(1).strip()
        print(f"Experience Section Content (first 500 chars):\n{experience_content[:500]}...\n")

        exp_item_pattern = re.compile(
            r'(?:^|\n)\s*'
            r'([\w\s&,./-]+\b(?:Engineer|Developer|Manager|Scientist|Analyst|Consultant|Architect|Designer|Specialist|Lead|Director|Physician|Doctor|Surgeon|Practitioner|Dentist|Resident|Fellow))\b'
            r'(?:(?:\s*at\s*|\s*,\s*)'
            r'([\w\s&,./-]+\b(?:Company|Corp|Inc|LLC|Ltd|Group|Solutions|Systems|Technologies|Hospital|Clinic|Medical Center))?\b)?'
            r'(?:[\s,\-]+(\d{4}(?:\s*[\-–]?\s*(?:\d{4}|Present|Current))?)\b)?'
            r'(.*?)(?=\n(?:[\w\s&,./-]+\b(?:Engineer|Developer|Manager|Scientist|Analyst|Consultant|Architect|Designer|Specialist|Lead|Director|Physician|Doctor|Surgeon|Practitioner|Dentist|Resident|Fellow))|\n{2,}|$)',
            re.IGNORECASE | re.DOTALL | re.MULTILINE
        )
        
        job_entries = re.split(
            r'\n(?=[\w\s&,./-]+\b(?:Engineer|Developer|Manager|Scientist|Analyst|Consultant|Architect|Designer|Specialist|Lead|Director|Physician|Doctor|Surgeon|Practitioner|Dentist|Resident|Fellow))|\n{2,}',
            experience_content,
            flags=re.IGNORECASE | re.MULTILINE
        )
        job_entries = [entry.strip() for entry in job_entries if entry.strip()]

        for entry_block in job_entries:
            match = exp_item_pattern.search(entry_block)
            if match:
                title = match.group(1)
                company = match.group(2)
                years = match.group(3)
                description_raw = match.group(4)

                description = re.sub(r'[\*\-•]\s*', '', description_raw).strip()
                description = re.sub(r'\s{2,}', ' ', description).strip()
                
                exp_entry = Experience(
                    title=title.strip() if title else None,
                    company=company.strip() if company else None,
                    years=years.strip() if years else None,
                    description=description if description else None
                )
                experience_list.append(exp_entry)
                print(f"  Found Experience: {exp_entry.model_dump_json()}")
            else:
                print(f"  No Exp Pattern Match for entry block:\n---\n{entry_block[:200]}...\n---\n")
    else:
        print("  No Experience section header found.")
    
    print(f"--- Finished Experience Extraction. Found {len(experience_list)} entries. ---")
    return experience_list


def parse_resume_file(resume_text: str, user_id: Optional[str] = None) -> CandidateProfile:
    if nlp is None:
        print("SpaCy model not loaded, cannot parse resumes.")
        return CandidateProfile(raw_text="Error: SpaCy model not loaded.", user_id=user_id)

    cleaned_text = clean_text(resume_text)
    
    if not cleaned_text.strip():
        print("Warning: No usable text extracted or cleaned from resume.")
        return CandidateProfile(raw_text="Error: No usable text extracted or cleaned.", user_id=user_id)

    doc = nlp(cleaned_text)

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    total_experience_years: Optional[float] = None

    first_few_lines = "\n".join(cleaned_text.split('\n')[:7])
    print(f"Parser: Name search area (first few lines):\n---\n{first_few_lines[:300]}...\n---\n")

    name_pattern_line = re.compile(r'^\s*([A-Z][a-z]+(?:[\s-][A-Z][a-z]+){0,3}(?:\s+[A-Z]\.?)?)\s*$', re.MULTILINE)
    name_match = name_pattern_line.search(first_few_lines)
    if name_match:
        name = name_match.group(1).strip()
        print(f"Parser: Name (Line Pattern) detected: {name}")
    else:
        name_pattern_general = re.compile(r'\b([A-Z][a-z]+(?:[\s-][A-Z][a-z]+){1,3})\b')
        general_name_match = name_pattern_general.search(first_few_lines)
        if general_name_match:
            name = general_name_match.group(1).strip()
            print(f"Parser: Name (General Pattern) detected: {name}")
        else:
            name_search_area = cleaned_text[:500]
            name_doc = nlp(name_search_area)
            person_entities = [ent.text.strip() for ent in name_doc.ents if ent.label_ == "PERSON" and len(ent.text.split()) >= 2]
            
            if person_entities:
                name = sorted(person_entities, key=len)[0]
                print(f"Parser: Name (SpaCy Fallback) detected: {name}")
            else:
                print("Parser: No clear name detected by patterns or spaCy.")

    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', cleaned_text)
    if email_match:
        email = email_match.group(0)
        print(f"Parser: Email detected: {email}")

    phone_match = re.search(r'(\+?\d{1,3}[\s.\-]?)?(\(?\d{3}\)?[\s.\-]?)?\d{3}[\s.\-]?\d{4}\b', cleaned_text)
    if phone_match:
        phone = phone_match.group(0)
        print(f"Parser: Phone detected: {phone}")

    tech_skills = ["python", "java", "c++", "javascript", "react", "angular", "node.js", "sql", "nosql",
                   "aws", "azure", "gcp", "docker", "kubernetes", "git", "linux", "machine learning",
                   "deep learning", "tensorflow", "pytorch", "data science", "tableau", "excel",
                   "html", "css", "api", "rest", "flask", "fastapi", "django", "scikit-learn", "numpy", "pandas"]
    
    cleaned_text_lower = cleaned_text.lower()
    skills = sorted(list(set([skill for skill in tech_skills if skill in cleaned_text_lower])))
    if skills:
        print(f"Parser: Skills detected: {skills}")
    else:
        print("Parser: No tech skills from predefined list detected.")

    extracted_education = extract_education(cleaned_text)
    extracted_experience = extract_experience(cleaned_text)

    total_duration_months = 0
    current_year = datetime.now().year
    
    for exp in extracted_experience:
        if exp.years:
            years_in_exp = parse_years_from_date_string(exp.years)
            if len(years_in_exp) == 2:
                start_year, end_year = years_in_exp
                if start_year <= end_year:
                    total_duration_months += (end_year - start_year + 1) * 12
            elif len(years_in_exp) == 1:
                total_duration_months += 12
            
    total_experience_years = round(total_duration_months / 12, 1) if total_duration_months > 0 else 0.0
    print(f"Parser: Calculated total experience: {total_experience_years} years")

    temp_profile = CandidateProfile(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        total_experience_years=total_experience_years,
        skills=skills,
        education=extracted_education,
        experience=extracted_experience,
        raw_text=resume_text
    )

    embedding_text = create_candidate_embedding_text(temp_profile)
    profile_embedding = generate_text_embedding(embedding_text)

    return CandidateProfile(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        total_experience_years=total_experience_years,
        skills=skills,
        education=extracted_education,
        experience=extracted_experience,
        raw_text=resume_text,
        embedding=profile_embedding
    )

if __name__ == "__main__":
    print("--- Running Parser Test with Full Extraction & Embeddings ---")
    sample_resume_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../data/resumes/resume_data_scientist.pdf")
    
    if os.path.exists(sample_resume_path):
        print(f"Loading text from {sample_resume_path}")
        raw_text_from_file = extract_text_from_pdf(sample_resume_path)
        parsed_data = parse_resume_file(raw_text_from_file, user_id="test_user_from_parser")
        print("--- Parsed Resume Data with Full Details & Embedding ---")
        print(parsed_data.model_dump_json(indent=2))
        if parsed_data.embedding:
            print(f"Embedding length: {len(parsed_data.embedding)}")
        else:
            print("No embedding generated.")
    else:
        print(f"Error: Sample resume not found at {sample_resume_path}.")
        print("Please ensure 'data/resumes/resume_data_scientist.pdf' exists relative to your project structure and has education/experience sections.")