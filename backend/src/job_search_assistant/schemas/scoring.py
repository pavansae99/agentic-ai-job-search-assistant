"""Explainable job-match scoring schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field


class FitCategory(StrEnum):
    """Human-readable recommendation derived from a deterministic score."""

    STRONG_FIT = "Strong Fit"
    GOOD_FIT = "Good Fit"
    WEAK_FIT = "Weak Fit"
    NOT_RECOMMENDED = "Not Recommended"


class ScoreBreakdown(BaseModel):
    """Component scores and their weighted final result."""

    skill_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    location_score: float = Field(ge=0, le=100)
    authorization_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    weights: dict[str, float]
    explanations: dict[str, str]
