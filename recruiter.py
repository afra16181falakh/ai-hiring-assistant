from fastapi import APIRouter, Depends, HTTPException, status, Path, UploadFile, File
from typing import List
import uuid

from app.schemas import (
    JobDescription,
    JobDescriptionCreate,
    CandidateProfile,
    RankedCandidateResponse,
    InterviewRequest,
    User # Keep User import as it might be used if auth is re-enabled
)
from app.core.database import jobs_db, candidates_db
# from app.auth import get_current_recruiter_user # Authentication dependency (currently commented out)
from app.parser import parse_resume_file
from app.ai_matcher import rank_candidates, generate_text_embedding, create_job_embedding_text
from app.utils import read_uploaded_file_to_text

router = APIRouter(prefix="/recruiter", tags=["Recruiter"])

@router.post("/jobs", response_model=JobDescription, status_code=status.HTTP_201_CREATED)
# async def create_job(job_data: JobDescriptionCreate, current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def create_job(job_data: JobDescriptionCreate): # TEMP: No auth for testing
    """Create a new job description."""
    job_embedding_text = create_job_embedding_text(JobDescription(**job_data.model_dump()))
    job_embedding = generate_text_embedding(job_embedding_text)

    new_job = JobDescription(id=str(uuid.uuid4()), **job_data.model_dump(), embedding=job_embedding)
    jobs_db[new_job.id] = new_job
    return new_job

@router.get("/jobs", response_model=List[JobDescription])
# async def get_all_jobs_recruiter_view(current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def get_all_jobs_recruiter_view(): # TEMP: No auth for testing
    """Retrieve a list of all job descriptions."""
    return list(jobs_db.values())

@router.get("/jobs/{job_id}", response_model=JobDescription)
# async def get_job_recruiter_view(job_id: str = Path(...), current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def get_job_recruiter_view(job_id: str = Path(...)): # TEMP: No auth for testing
    """Retrieve details for a specific job."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/jobs/{job_id}", response_model=JobDescription)
# async def update_job(job_id: str, job_data: JobDescriptionCreate, current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def update_job(job_id: str, job_data: JobDescriptionCreate): # TEMP: No auth for testing
    """Update an existing job description."""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_embedding_text = create_job_embedding_text(JobDescription(**job_data.model_dump()))
    job_embedding = generate_text_embedding(job_embedding_text)

    updated_job = JobDescription(id=job_id, **job_data.model_dump(), embedding=job_embedding)
    jobs_db[job_id] = updated_job
    return updated_job

@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_job(job_id: str, current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def delete_job(job_id: str): # TEMP: No auth for testing
    """Delete a job description."""
    if job_id in jobs_db:
        del jobs_db[job_id]
        return {"message": "Job deleted successfully"}
    raise HTTPException(status_code=404, detail="Job not found")

@router.post("/jobs/{job_id}/process_resumes", response_model=List[RankedCandidateResponse])
# async def process_resumes_for_job(job_id: str = Path(...), resumes: List[UploadFile] = File(...), current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def process_resumes_for_job(job_id: str = Path(...), resumes: List[UploadFile] = File(...)): # TEMP: No auth for testing
    """
    Uploads and processes multiple resumes for a specific job.
    Parses each resume, creates candidate profiles, and ranks them against the job description.
    """
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. Please create the job first.")
    
    if not resumes:
        raise HTTPException(status_code=400, detail="No resume files provided.")

    job_description_text = job.description
    candidate_profiles_for_ranking: List[CandidateProfile] = []
    
    for resume_file in resumes:
        try:
            resume_text = await read_uploaded_file_to_text(resume_file)
            profile = parse_resume_file(resume_text, user_id=None)
            
            if profile and profile.raw_text and profile.raw_text.strip():
                candidates_db[profile.id] = profile
                candidate_profiles_for_ranking.append(profile)
                if profile.id not in job.processed_candidate_profiles_ids:
                    job.processed_candidate_profiles_ids.append(profile.id)
            else:
                print(f"Warning: Resume {resume_file.filename} parsed to an empty or invalid profile.")
        except Exception as e:
            print(f"Error processing resume {resume_file.filename}: {e}")

    if not candidate_profiles_for_ranking:
        raise HTTPException(status_code=500, detail="No resumes could be parsed successfully or no valid profiles extracted.")

    ranked_results = rank_candidates(job, candidate_profiles_for_ranking)

    if not ranked_results:
        raise HTTPException(status_code=500, detail="Candidate ranking failed or returned no results.")

    return ranked_results

@router.get("/jobs/{job_id}/ranked_candidates", response_model=List[RankedCandidateResponse])
# async def get_ranked_candidates_for_job(job_id: str = Path(...), current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def get_ranked_candidates_for_job(job_id: str = Path(...)): # TEMP: No auth for testing
    """Retrieve ranked candidates for a specific job."""
    job = jobs_db.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    if not job.processed_candidate_profiles_ids:
        raise HTTPException(status_code=404, detail="No candidates have been processed for this job yet.")

    candidates_for_job = [candidates_db[cid] for cid in job.processed_candidate_profiles_ids if cid in candidates_db]
    
    if not candidates_for_job:
        raise HTTPException(status_code=500, detail="No valid candidate profiles found for this job.")

    ranked_results = rank_candidates(job, candidates_for_job)

    if not ranked_results:
        raise HTTPException(status_code=500, detail="Ranking could not be performed or returned no results.")

    return ranked_results

@router.post("/schedule_interview", status_code=status.HTTP_202_ACCEPTED)
# async def schedule_interview_trigger(request: InterviewRequest, current_recruiter: User = Depends(get_current_recruiter_user)): # Original with auth
async def schedule_interview_trigger(request: InterviewRequest): # TEMP: No auth for testing
    """
    Initiates an interview scheduling request for a candidate for a specific job.
    """
    job = jobs_db.get(request.job_id)
    candidate_profile = candidates_db.get(request.candidate_profile_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID '{request.job_id}' not found.")
    if not candidate_profile:
        raise HTTPException(status_code=404, detail=f"Candidate profile with ID '{request.candidate_profile_id}' not found.")
    if not request.interviewer_ids:
        raise HTTPException(status_code=400, detail="At least one interviewer ID is required.")
    if not request.preferred_dates_times:
        raise HTTPException(status_code=400, detail="Preferred dates/times are required for scheduling.")

    print(f"\n--- SCHEDULING REQUEST RECEIVED ---")
    print(f"Job: {job.title} ({job.id})")
    print(f"Candidate Profile: {candidate_profile.name} ({candidate_profile.id})")
    print(f"Candidate User ID (if linked): {candidate_profile.user_id}")
    print(f"Interviewers: {request.interviewer_ids}")
    print(f"Preferred Times: {request.preferred_dates_times}")
    print(f"Notes: {request.notes or 'None'}")
    print(f"--- Handing off to scheduling service... (Chaithanya's part) ---\n")

    return {"message": "Interview scheduling request received and being processed asynchronously."}