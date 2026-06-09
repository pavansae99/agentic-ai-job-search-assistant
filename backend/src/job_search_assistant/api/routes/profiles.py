"""Candidate profile analysis endpoint."""

from fastapi import APIRouter

from job_search_assistant.api.dependencies import ProfileAnalysisServiceDependency
from job_search_assistant.schemas.profile import ProfileAnalysisResponse, ProfileAnalyzeRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/analyze", response_model=ProfileAnalysisResponse)
def analyze_profile(
    payload: ProfileAnalyzeRequest,
    service: ProfileAnalysisServiceDependency,
) -> ProfileAnalysisResponse:
    """Extract a structured profile and profile-completeness suggestions."""

    return service.analyze(payload.raw_resume_text)
