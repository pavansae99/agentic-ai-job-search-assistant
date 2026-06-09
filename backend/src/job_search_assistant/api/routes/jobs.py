"""Job analysis and matching endpoints."""

from fastapi import APIRouter

from job_search_assistant.api.dependencies import JobAnalysisServiceDependency
from job_search_assistant.schemas.job import (
    JobAnalysisResponse,
    JobAnalyzeRequest,
    JobMatchRequest,
    JobMatchResponse,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/analyze", response_model=JobAnalysisResponse)
def analyze_job(
    payload: JobAnalyzeRequest,
    service: JobAnalysisServiceDependency,
) -> JobAnalysisResponse:
    """Parse a job description into normalized requirements."""

    return service.analyze(payload.raw_job_description)


@router.post("/match", response_model=JobMatchResponse)
def match_job(
    payload: JobMatchRequest,
    service: JobAnalysisServiceDependency,
) -> JobMatchResponse:
    """Execute the complete LangGraph resume-to-job workflow."""

    return service.match(
        raw_resume_text=payload.raw_resume_text,
        raw_job_description=payload.raw_job_description,
    )
