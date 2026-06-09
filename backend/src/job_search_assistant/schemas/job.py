"""Job parsing and match response schemas."""

from pydantic import BaseModel, Field, field_validator

from job_search_assistant.schemas.profile import CandidateProfile, NonEmptyText, normalized_strings
from job_search_assistant.schemas.scoring import FitCategory, ScoreBreakdown


class ParsedJob(BaseModel):
    """Structured requirements extracted from a job description."""

    title: str = "Unknown role"
    company: str = "Unknown company"
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    minimum_years_experience: float = Field(default=0, ge=0, le=80)
    location: str = "Not specified"
    work_authorization_requirement: str = "not specified"
    summary: str = ""

    _normalize_skills = field_validator("required_skills", "preferred_skills")(normalized_strings)


class JobAnalyzeRequest(BaseModel):
    """Request to parse a raw job description."""

    raw_job_description: NonEmptyText


class JobAnalysisResponse(BaseModel):
    """Structured job requirements."""

    job: ParsedJob
    reasoning_trace: list[str]


class JobMatchRequest(BaseModel):
    """Request to run the end-to-end agent workflow."""

    raw_resume_text: NonEmptyText
    raw_job_description: NonEmptyText


class JobMatchResponse(BaseModel):
    """Complete, explainable workflow result."""

    parsed_profile: CandidateProfile
    parsed_job: ParsedJob
    scoring: ScoreBreakdown
    ranking: FitCategory
    missing_keywords: list[str]
    recruiter_email: str
    career_suggestions: list[str]
    reasoning_trace: list[str]
