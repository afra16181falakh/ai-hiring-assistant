from fastapi import APIRouter, HTTPException, status, Path, UploadFile, File, Query
from typing import List
from datetime import datetime, timezone
import uuid

from app.schemas import (
    JobDescription,
    CandidateProfile,
    CandidateApplication,
    ApplicationStatus,
    CandidateAvailability,
)
from app.core.database import jobs_db, candidates_db, applications_db
from app.parser import parse_resume_file
from app.utils import read_uploaded_file_to_text

router = APIRouter(prefix="/candidate", tags=["Candidate"])

@router.get("/jobs", response_model=List[JobDescription])
async def get_public_jobs():
    return [job for job in jobs_db.values() if job.is_public]

@router.get("/jobs/{job_id}", response_model=JobDescription)
async def get_public_job_details(job_id: str = Path(...)):
    job = jobs_db.get(job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=404, detail="Public job not found")
    return job

@router.post("/apply/{job_id}", response_model=CandidateApplication, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_id: str = Path(...),
    resume_file: UploadFile = File(...),
    candidate_user_id: str = Query("test_candidate_user_001", description="Dummy user ID for testing without authentication")
):
    job = jobs_db.get(job_id)
    if not job or not job.is_public:
        raise HTTPException(status_code=404, detail="Job not found or not open for public applications.")

    for app_entry in applications_db.values():
        if app_entry.candidate_user_id == candidate_user_id and app_entry.job_id == job_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You have already applied for this job.")

    try:
        resume_text = await read_uploaded_file_to_text(resume_file)
        candidate_profile = parse_resume_file(resume_text, user_id=candidate_user_id)
        
        if not (candidate_profile and candidate_profile.raw_text and candidate_profile.raw_text.strip()):
            raise ValueError("Resume parsing failed or resulted in empty content.")

        candidates_db[candidate_profile.id] = candidate_profile

        new_application = CandidateApplication(
            id=str(uuid.uuid4()),
            candidate_user_id=candidate_user_id,
            job_id=job_id,
            candidate_profile_id=candidate_profile.id,
            status=ApplicationStatus.APPLIED,
            applied_at=datetime.now(timezone.utc)
        )
        applications_db[new_application.id] = new_application

        return new_application

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error during application for job {job_id} by candidate {candidate_user_id}: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during application processing.")

@router.get("/{candidate_user_id}/applications", response_model=List[CandidateApplication])
async def get_candidate_applications(
    candidate_user_id: str = Path(...),
):
    return [app_entry for app_entry in applications_db.values() if app_entry.candidate_user_id == candidate_user_id]

@router.post("/{candidate_user_id}/submit_availability", status_code=status.HTTP_202_ACCEPTED)
async def submit_candidate_availability(
    availability_data: CandidateAvailability,
    candidate_user_id: str = Path(...),
):
    found_application_for_job = False
    for app_obj in applications_db.values():
        if app_obj.candidate_user_id == candidate_user_id and app_obj.job_id == availability_data.job_id:
            found_application_for_job = True
            break
    
    if not found_application_for_job:
        raise HTTPException(status_code=400, detail=f"Candidate has not applied for job '{availability_data.job_id}'.")

    print(f"\n--- CANDIDATE AVAILABILITY RECEIVED ---")
    print(f"Candidate User: {candidate_user_id}")
    print(f"Job: {availability_data.job_id}")
    print(f"Available Slots: {availability_data.available_slots}")
    print(f"Notes: {availability_data.notes or 'None'}")
    print(f"--- Handing off to scheduling matching service... (Chaithanya's part) ---\n")

    return {"message": "Candidate availability received and will be processed."}

@router.get("/profiles/{candidate_profile_id}", response_model=CandidateProfile)
async def get_candidate_profile(
    candidate_profile_id: str = Path(...),
):
    candidate_profile = candidates_db.get(candidate_profile_id)
    if not candidate_profile:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")
    
    return candidate_profile.model_dump(exclude={"raw_text"})