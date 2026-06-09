"""Candidate profile schemas."""

from typing import Annotated

from pydantic import BaseModel, Field, field_validator

NonEmptyText = Annotated[str, Field(min_length=20, max_length=100_000)]


def normalized_strings(values: list[str]) -> list[str]:
    """Strip, de-duplicate, and preserve the order of string values."""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)
    return result


class CandidateProfile(BaseModel):
    """Structured facts extracted from a resume."""

    skills: list[str] = Field(default_factory=list)
    years_of_experience: float = Field(default=0, ge=0, le=80)
    target_roles: list[str] = Field(default_factory=list)
    location_preferences: list[str] = Field(default_factory=list)
    work_authorization: str = "not specified"
    summary: str = ""

    _normalize_lists = field_validator(
        "skills",
        "target_roles",
        "location_preferences",
    )(normalized_strings)


class ProfileAnalyzeRequest(BaseModel):
    """Request to parse and assess a resume."""

    raw_resume_text: NonEmptyText


class ProfileAnalysisResponse(BaseModel):
    """Structured profile plus actionable career coaching."""

    profile: CandidateProfile
    career_suggestions: list[str]
    reasoning_trace: list[str]
