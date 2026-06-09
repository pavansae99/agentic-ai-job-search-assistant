"""Structured-output schemas used only at the LLM provider boundary."""

from enum import StrEnum

from pydantic import BaseModel, Field

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile


class LLMOperation(StrEnum):
    """Stable identifiers for provider-backed workflow operations."""

    RESUME_EXTRACTION = "resume_extraction"
    JOB_EXTRACTION = "job_extraction"
    RECRUITER_EMAIL = "recruiter_email"


class LLMProviderMetadata(BaseModel):
    """Internal provenance metadata attached to reasoning traces."""

    provider: str
    model: str
    prompt_version: str
    operation: LLMOperation

    def trace_fragment(self) -> str:
        """Render metadata without exposing prompts, input text, or credentials."""

        return f"provider={self.provider} model={self.model} prompt_version={self.prompt_version}"


class ResumeProfileExtraction(BaseModel):
    """LLM response for resume fact extraction."""

    skills: list[str]
    years_of_experience: float = Field(ge=0, le=80)
    target_roles: list[str]
    location_preferences: list[str]
    work_authorization: str
    summary: str

    def to_domain(self) -> CandidateProfile:
        """Convert provider output into the stable domain schema."""

        return CandidateProfile.model_validate(self.model_dump())


class JobRequirementsExtraction(BaseModel):
    """LLM response for job requirement extraction."""

    title: str
    company: str
    required_skills: list[str]
    preferred_skills: list[str]
    minimum_years_experience: float = Field(ge=0, le=80)
    location: str
    work_authorization_requirement: str
    summary: str

    def to_domain(self) -> ParsedJob:
        """Convert provider output into the stable domain schema."""

        return ParsedJob.model_validate(self.model_dump())


class RecruiterEmailDraft(BaseModel):
    """Structured recruiter email returned by an LLM."""

    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5_000)

    def render(self) -> str:
        """Render the structured draft into the existing API string contract."""

        return f"Subject: {self.subject.strip()}\n\n{self.body.strip()}"
