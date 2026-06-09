"""Tests for weighted scoring and ranking."""

import pytest

from job_search_assistant.agents.fit_ranking_agent import FitRankingAgent
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory
from job_search_assistant.services.match_scoring_service import MatchScoringService


def test_scoring_returns_explainable_weighted_score() -> None:
    profile = CandidateProfile(
        skills=["Python", "Kafka", "Kubernetes"],
        years_of_experience=6,
        location_preferences=["Remote"],
        work_authorization="Authorized to work in the US without sponsorship",
    )
    job = ParsedJob(
        required_skills=["Python", "Kafka", "Go", "Kubernetes"],
        minimum_years_experience=8,
        location="Remote",
        work_authorization_requirement="US work authorization required; sponsorship unavailable",
    )

    scoring = MatchScoringService().score(profile, job)

    assert scoring.skill_score == 75
    assert scoring.experience_score == 75
    assert scoring.location_score == 100
    assert scoring.authorization_score == 100
    assert scoring.final_score == 82.5
    assert MatchScoringService.missing_keywords(profile, job) == ["Go"]
    assert scoring.explanations["skills"] == "Matched 3 of 4 required skills."


def test_scoring_detects_authorization_and_location_risk() -> None:
    profile = CandidateProfile(
        skills=["Python"],
        years_of_experience=2,
        location_preferences=["Chicago"],
        work_authorization="Requires visa sponsorship",
    )
    job = ParsedJob(
        required_skills=["Python"],
        minimum_years_experience=4,
        location="New York",
        work_authorization_requirement="US work authorization required; sponsorship unavailable",
    )

    scoring = MatchScoringService().score(profile, job)

    assert scoring.experience_score == 50
    assert scoring.location_score == 25
    assert scoring.authorization_score == 0


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (85, FitCategory.STRONG_FIT),
        (84.99, FitCategory.GOOD_FIT),
        (70, FitCategory.GOOD_FIT),
        (50, FitCategory.WEAK_FIT),
        (49.99, FitCategory.NOT_RECOMMENDED),
    ],
)
def test_ranking_thresholds(score: float, expected: FitCategory) -> None:
    assert FitRankingAgent().run(score) is expected
