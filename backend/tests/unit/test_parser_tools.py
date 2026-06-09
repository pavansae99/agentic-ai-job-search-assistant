"""Tests for deterministic resume and job parser tools."""

from job_search_assistant.tools.job_parser_tool import JobParserTool
from job_search_assistant.tools.resume_parser_tool import ResumeParserTool


def test_resume_parser_extracts_candidate_profile(sample_resume: str) -> None:
    profile = ResumeParserTool().parse(sample_resume)

    assert profile.years_of_experience == 9
    assert "Go" in profile.skills
    assert "Python" in profile.skills
    assert profile.target_roles[0] == "Senior Software Engineer"
    assert profile.location_preferences == ["Chicago", "Remote"]
    assert "without sponsorship" in profile.work_authorization


def test_resume_parser_handles_sparse_resume() -> None:
    profile = ResumeParserTool().parse(
        "Backend developer focused on reliable software delivery and product outcomes."
    )

    assert profile.years_of_experience == 0
    assert profile.skills == []
    assert profile.target_roles == []
    assert profile.work_authorization == "not specified"


def test_job_parser_extracts_required_and_preferred_skills(sample_job: str) -> None:
    job = JobParserTool().parse(sample_job)

    assert job.company == "Acme Cloud"
    assert job.title == "Senior Backend Engineer"
    assert job.minimum_years_experience == 7
    assert "Kubernetes" in job.required_skills
    assert "LangGraph" in job.preferred_skills
    assert job.location == "Remote - United States"
    assert "sponsorship unavailable" in job.work_authorization_requirement


def test_job_parser_infers_defaults() -> None:
    job = JobParserTool().parse(
        "Join our remote product team to build accessible customer-facing software."
    )

    assert job.title == "Unknown role"
    assert job.company == "Unknown company"
    assert job.location == "Remote"
    assert job.required_skills == []
