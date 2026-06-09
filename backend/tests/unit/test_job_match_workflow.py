"""Tests for the complete typed LangGraph workflow."""

from job_search_assistant.schemas.scoring import FitCategory
from job_search_assistant.workflows.job_match_workflow import JobMatchWorkflow


def test_workflow_happy_path(sample_resume: str, sample_job: str) -> None:
    result = JobMatchWorkflow().run(sample_resume, sample_job)

    assert result.parsed_profile.years_of_experience == 9
    assert result.parsed_job.company == "Acme Cloud"
    assert result.scoring.final_score >= 85
    assert result.ranking is FitCategory.STRONG_FIT
    assert result.missing_keywords == []
    assert "Acme Cloud" in result.recruiter_email
    assert len(result.reasoning_trace) == 6
