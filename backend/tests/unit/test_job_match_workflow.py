"""Tests for the complete typed LangGraph workflow."""

from job_search_assistant.llm.schemas import LLMOperation, LLMProviderMetadata
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
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


class StubProvider:
    """Provider double proving that graph agents use dependency injection."""

    name = "stub"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile:
        self.calls.append(f"resume:{raw_resume_text}")
        return CandidateProfile(
            skills=["Python", "Kafka"],
            years_of_experience=8,
            target_roles=["Platform Engineer"],
            location_preferences=["Remote"],
            work_authorization="Authorized to work in the US without sponsorship",
        )

    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob:
        self.calls.append(f"job:{raw_job_description}")
        return ParsedJob(
            title="Senior Platform Engineer",
            company="Example Cloud",
            required_skills=["Python", "Kafka"],
            minimum_years_experience=5,
            location="Remote",
            work_authorization_requirement="US work authorization required",
        )

    def generate_recruiter_email(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        self.calls.append(f"email:{ranking.value}:{','.join(matched_skills)}")
        return "Subject: Provider-generated draft\n\nGrounded body"

    def metadata_for(self, operation: LLMOperation) -> LLMProviderMetadata:
        return LLMProviderMetadata(
            provider=self.name,
            model="stub-model",
            prompt_version=f"stub-{operation.value}-v1",
            operation=operation,
        )

    def close(self) -> None:
        pass


def test_workflow_uses_injected_provider_and_preserves_scoring() -> None:
    provider = StubProvider()

    result = JobMatchWorkflow(llm_provider=provider).run("resume input", "job input")

    assert result.scoring.final_score == 100
    assert result.ranking is FitCategory.STRONG_FIT
    assert result.recruiter_email.startswith("Subject: Provider-generated")
    assert provider.calls == [
        "resume:resume input",
        "job:job input",
        "email:Strong Fit:Python,Kafka",
    ]
    assert all("provider=stub" in trace for trace in result.reasoning_trace[:2])
    assert "provider=stub" in result.reasoning_trace[4]
    assert all("model=stub-model" in trace for trace in result.reasoning_trace[:2])
    assert "prompt_version=stub-recruiter_email-v1" in result.reasoning_trace[4]
