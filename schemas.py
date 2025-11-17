from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid
from enum import Enum
from datetime import datetime, timezone

class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None

class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    years: Optional[str] = None
    description: Optional[str] = None

class CandidateProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    total_experience_years: Optional[float] = None
    skills: List[str] = []
    education: List[Education] = []
    experience: List[Experience] = []
    raw_text: Optional[str] = None
    embedding: Optional[List[float]] = None

class JobDescriptionBase(BaseModel):
    title: str
    description: str
    posted_by: Optional[str] = "Recruiter"
    is_public: bool = True

class JobDescriptionCreate(JobDescriptionBase):
    pass

class JobDescription(JobDescriptionBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processed_candidate_profiles_ids: List[str] = []
    embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True

class InterviewRequest(BaseModel):
    job_id: str
    candidate_profile_id: str
    interviewer_ids: List[str]
    preferred_dates_times: List[str]
    notes: Optional[str] = None

class RankedCandidateResponse(BaseModel):
    candidate_profile: CandidateProfile
    match_score: float
    explainability: Dict

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_profile": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "another-uuid-string",
                    "name": "Jane Doe",
                    "email": "jane.doe@example.com",
                    "phone": "123-456-7890",
                    "total_experience_years": 5.0,
                    "skills": ["Python", "Machine Learning", "FastAPI"],
                    "education": [],
                    "experience": [],
                    "embedding": []
                },
                "match_score": 85.5,
                "explainability": {
                    "matched_skills": ["python", "machine learning"],
                    "common_keywords_in_resume": ["data", "engineer"],
                    "total_experience": "5.0 years"
                }
            }
        }

class UserRole(str, Enum):
    RECRUITER = "recruiter"
    CANDIDATE = "candidate"
    ADMIN = "admin"

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.CANDIDATE

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    password: str
    role: UserRole
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    UNDER_REVIEW = "Under Review"
    SHORTLISTED = "Shortlisted"
    INTERVIEW_SCHEDULED = "Interview Scheduled"
    REJECTED = "Rejected"
    HIRED = "Hired"

class CandidateApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    candidate_user_id: str
    job_id: str
    candidate_profile_id: str
    status: ApplicationStatus = ApplicationStatus.APPLIED
    applied_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CandidateAvailability(BaseModel):
    candidate_id: str
    job_id: str
    available_slots: List[str]
    notes: Optional[str] = None