"""Tests for workflow agents outside the core parsing and scoring path."""

from job_search_assistant.agents.career_coach_agent import CareerCoachAgent
from job_search_assistant.agents.recruiter_email_agent import RecruiterEmailAgent
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory, ScoreBreakdown


def test_recruiter_email_agent_uses_matched_skills_only() -> None:
    profile = CandidateProfile(
        skills=["Python", "Kafka"],
        years_of_experience=8,
        target_roles=["Senior Software Engineer"],
    )
    job = ParsedJob(
        title="Platform Engineer",
        company="Example Corp",
        required_skills=["Python", "Kafka", "Go"],
    )

    email = RecruiterEmailAgent().run(profile, job, FitCategory.GOOD_FIT, ["Go"])

    assert "Platform Engineer at Example Corp" in email
    assert "Python, Kafka" in email
    assert "Go," not in email


def test_career_coach_returns_profile_and_match_advice() -> None:
    coach = CareerCoachAgent()
    sparse_profile = CandidateProfile()

    assert len(coach.review_profile(sparse_profile)) == 4

    job = ParsedJob(location="Hybrid", required_skills=["Python"])
    scoring = ScoreBreakdown(
        skill_score=0,
        experience_score=50,
        location_score=60,
        authorization_score=50,
        final_score=35,
        weights={},
        explanations={},
    )
    suggestions = coach.review_match(sparse_profile, job, scoring, ["Python"])

    assert len(suggestions) == 4
    assert "Python" in suggestions[0]
