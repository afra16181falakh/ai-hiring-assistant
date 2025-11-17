AI Hiring Assistant

The AI Hiring Assistant is an intelligent recruitment automation system designed to streamline the hiring process for recruiters and candidates.
It uses AI-driven resume parsing, smart candidate–job matching, and automated interview scheduling to reduce manual effort and accelerate end-to-end hiring.

This project is built as part of a hackathon initiative with a goal of creating a scalable and modular hiring assistant that can be extended into a full-fledged recruitment platform.


Key Features

1. AI-Powered Resume Parsing
	•	Extracts name, email, phone, skills, and text from PDF/TXT resumes.
	•	Converts raw resumes into structured JSON for downstream processing.

2. JD–Candidate Matching (AI Ranking)
	•	Uses sentence embeddings (Sentence Transformers) to compare JDs with resumes.
	•	Ranks candidates based on:
	•	Skill match %
	•	JD similarity score
	•	Highlighted matched skills (explainability)

3. Scheduling System (Stub)
	•	Simple API to simulate interview slot confirmation.
	•	Future upgrade → Real Outlook Calendar integration via Microsoft Graph API.

4. Candidate Availability Module
	•	Candidate can submit time slots.
	•	Data saved for scheduling and ranking logic.

5. API-First Architecture
	•	Clean FastAPI-based backend.
	•	Ready to plug into any frontend (React/Streamlit).

⸻

Tech Stack

Backend
	•	FastAPI – core backend framework
	•	Python
	•	PyMuPDF (fitz) – PDF text extraction
	•	Sentence Transformers – embeddings & ranking
	•	FAISS (planned) – vector store for fast search
	•	Uvicorn – server

Frontend (team modules)
	•	React.js / Streamlit

Dashboard
	•	Power BI / Tableau

Scheduling
	•	Microsoft Graph API (planned)
	•	Outlook / Google Calendar APIs

Dev Tools
	•	GitHub
	•	Virtual environment (venv)
	•	JSON-based data storage (for hackathon phase)

