"""Integration tests for provider startup validation and shared lifecycle."""

import pytest
from fastapi.testclient import TestClient

from job_search_assistant.container import ApplicationContainer
from job_search_assistant.core.settings import Settings
from job_search_assistant.llm.mock_provider import MockProvider
from job_search_assistant.llm.provider import LLMProviderConfigurationError
from job_search_assistant.main import create_app
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory


class TrackingProvider(MockProvider):
    """Deterministic provider that records reuse and shutdown."""

    def __init__(self) -> None:
        super().__init__()
        self.resume_calls = 0
        self.job_calls = 0
        self.email_calls = 0
        self.close_calls = 0

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile:
        self.resume_calls += 1
        return super().extract_resume_profile(raw_resume_text)

    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob:
        self.job_calls += 1
        return super().extract_job_requirements(raw_job_description)

    def generate_recruiter_email(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        self.email_calls += 1
        return super().generate_recruiter_email(
            profile,
            job,
            ranking,
            matched_skills,
        )

    def close(self) -> None:
        self.close_calls += 1


def test_application_reuses_and_closes_one_provider(
    sample_resume: str,
    sample_job: str,
) -> None:
    provider = TrackingProvider()
    factory_calls = 0

    def container_factory(_settings: Settings) -> ApplicationContainer:
        nonlocal factory_calls
        factory_calls += 1
        return ApplicationContainer.from_provider(provider)

    application = create_app(
        app_settings=Settings(llm_provider="mock"),
        container_factory=container_factory,
    )

    with TestClient(application) as client:
        profile_response = client.post(
            "/api/profile/analyze",
            json={"raw_resume_text": sample_resume},
        )
        job_response = client.post(
            "/api/jobs/analyze",
            json={"raw_job_description": sample_job},
        )
        match_response = client.post(
            "/api/jobs/match",
            json={
                "raw_resume_text": sample_resume,
                "raw_job_description": sample_job,
            },
        )

        assert profile_response.status_code == 200
        assert job_response.status_code == 200
        assert match_response.status_code == 200
        assert factory_calls == 1
        assert provider.resume_calls == 2
        assert provider.job_calls == 2
        assert provider.email_calls == 1
        assert provider.close_calls == 0

    assert provider.close_calls == 1


def test_explicit_openai_without_key_fails_during_startup() -> None:
    application = create_app(app_settings=Settings(llm_provider="openai", openai_api_key=None))

    with (
        pytest.raises(LLMProviderConfigurationError, match="OPENAI_API_KEY is required"),
        TestClient(application),
    ):
        pass
