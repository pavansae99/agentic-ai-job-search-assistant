"""Typed state shared by every job-search graph node."""

import operator
from typing import Annotated, TypedDict

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory, ScoreBreakdown


class JobMatchState(TypedDict, total=False):
    """The durable contract connecting workflow nodes."""

    raw_resume_text: str
    parsed_profile: CandidateProfile
    raw_job_description: str
    parsed_job: ParsedJob
    match_score: float
    scoring: ScoreBreakdown
    ranking: FitCategory
    missing_keywords: list[str]
    recruiter_email: str
    career_suggestions: list[str]
    reasoning_trace: Annotated[list[str], operator.add]
