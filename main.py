from fastapi import FastAPI
import os

from app.schemas import (
    CandidateProfile,
    JobDescription,
    JobDescriptionCreate,
    InterviewRequest,
    RankedCandidateResponse,
    User,
    UserCreate,
    UserRole,
    Token,
    CandidateApplication,
    ApplicationStatus,
    CandidateAvailability
)
from app.core.config import settings
from app.core.database import users_db, jobs_db, candidates_db, applications_db
# from app.auth import router as auth_router_instance # Auth router commented out
from app.routers.candidate import router as candidate_router_instance
from app.routers.recruiter import router as recruiter_router_instance


app = FastAPI(
    title=settings.APP_NAME,
    description="API for AI-powered resume screening, job management, and interview scheduling.",
    version=settings.APP_VERSION,
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# app.include_router(auth_router_instance, prefix="/auth", tags=["Auth"]) # Auth router commented out
app.include_router(candidate_router_instance)
app.include_router(recruiter_router_instance)

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} API is running! Go to /docs for API documentation."}