"""Candidate profile analysis endpoint."""

from fastapi import APIRouter

from job_search_assistant.schemas.profile import ProfileAnalysisResponse, ProfileAnalyzeRequest
from job_search_assistant.services.profile_analysis_service import ProfileAnalysisService

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/analyze", response_model=ProfileAnalysisResponse)
def analyze_profile(payload: ProfileAnalyzeRequest) -> ProfileAnalysisResponse:
    """Extract a structured profile and profile-completeness suggestions."""

    return ProfileAnalysisService().analyze(payload.raw_resume_text)
