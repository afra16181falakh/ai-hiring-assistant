from typing import Dict
from app.schemas import CandidateProfile, JobDescription, User, CandidateApplication, UserRole
import uuid
from app.ai_matcher import generate_text_embedding, create_job_embedding_text

jobs_db: Dict[str, JobDescription] = {}
candidates_db: Dict[str, CandidateProfile] = {}
users_db: Dict[str, User] = {}
applications_db: Dict[str, CandidateApplication] = {}

# Example data for initial testing

# Add public jobs with pre-computed embeddings
job_title_1 = "Senior Python Developer"
job_description_1 = "Looking for an experienced Python Developer with expertise in FastAPI and Machine Learning."
job_embedding_text_1 = create_job_embedding_text(
    JobDescription(title=job_title_1, description=job_description_1)
)
job_embedding_1 = generate_text_embedding(job_embedding_text_1)

job_id_1 = str(uuid.uuid4())
jobs_db[job_id_1] = JobDescription(
    id=job_id_1,
    title=job_title_1,
    description=job_description_1,
    posted_by="Recruiter",
    is_public=True,
    embedding=job_embedding_1
)

job_title_2 = "Data Scientist"
job_description_2 = "Seeking a Data Scientist with strong skills in data analysis, statistical modeling, and Python (Pandas, NumPy, Scikit-learn)."
job_embedding_text_2 = create_job_embedding_text(
    JobDescription(title=job_title_2, description=job_description_2)
)
job_embedding_2 = generate_text_embedding(job_embedding_text_2)

job_id_2 = str(uuid.uuid4())
jobs_db[job_id_2] = JobDescription(
    id=job_id_2,
    title=job_title_2,
    description=job_description_2,
    posted_by="Recruiter",
    is_public=True,
    embedding=job_embedding_2
)