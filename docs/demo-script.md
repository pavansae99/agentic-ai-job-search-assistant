# Two-Minute Demo Script

## 0:00-0:20: Problem And Design

"This project helps a candidate evaluate jobs and track applications. I designed it as a typed
multi-agent backend rather than a single prompt. FastAPI handles transport, LangGraph orchestrates
specialized agents, deterministic services own scoring policy, and SQLAlchemy persists the
application pipeline."

## 0:20-0:50: Profile And Job Analysis

Open `/docs` and run `POST /api/profile/analyze` with the sample resume.

"The ResumeAnalysisAgent extracts normalized skills, experience, role, location, and authorization.
It uses a local tool today, so the demo and tests need no API key. The same agent interface can
later use structured LLM output."

Run `POST /api/jobs/analyze` with the sample job.

"The JobAnalysisAgent separates core and preferred skills and extracts constraints that affect fit."

## 0:50-1:25: LangGraph Match

Run `POST /api/jobs/match`.

"This endpoint executes the actual LangGraph: resume parsing, job parsing, scoring, ranking, and
email generation. The score is 50% skills, 20% experience, 15% location, and 15% authorization.
Each component has an explanation. The reasoning trace shows node contributions without exposing
private chain-of-thought, and the email only mentions skills the candidate actually has."

Point to `src/job_search_assistant/workflows/job_match_state.py` and
`src/job_search_assistant/workflows/job_match_workflow.py`.

"Typed state makes node ownership visible and creates a clean path to checkpointing and human
approval."

## 1:25-1:45: Application Tracker

Create an application, list it, and patch its status to `interview`.

"The tracker uses a repository and service boundary, so moving from SQLite to PostgreSQL does not
change routes or agent logic."

## 1:45-2:00: Production Path

"The retrieval interface currently uses local cosine search and can be replaced by Chroma or
pgvector. The next production steps are model adapters with structured output, vector provenance,
LangGraph checkpoints, a human approval interrupt before outreach, authentication, and
observability. CI already enforces linting, formatting, strict typing, tests, and coverage."
