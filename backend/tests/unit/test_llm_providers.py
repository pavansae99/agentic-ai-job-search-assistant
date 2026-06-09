"""Tests for provider selection and structured LLM boundaries."""

from collections.abc import Iterator
from types import SimpleNamespace
from typing import cast

import httpx
import openai
import pytest
from openai import OpenAI
from pydantic import SecretStr, ValidationError

from job_search_assistant.core.settings import Settings
from job_search_assistant.llm.mock_provider import MockProvider
from job_search_assistant.llm.openai_provider import OpenAIProvider
from job_search_assistant.llm.prompts import (
    JOB_EXTRACTION_PROMPT_VERSION,
    RECRUITER_EMAIL_PROMPT_VERSION,
    RESUME_EXTRACTION_PROMPT_VERSION,
)
from job_search_assistant.llm.provider import (
    LLMProvider,
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderRefusalError,
    LLMProviderTimeoutError,
    LLMProviderTransientError,
    create_llm_provider,
)
from job_search_assistant.llm.schemas import (
    JobRequirementsExtraction,
    LLMOperation,
    RecruiterEmailDraft,
    ResumeProfileExtraction,
)
from job_search_assistant.schemas.scoring import FitCategory


def parsed_response(
    output_parsed: object,
    *,
    status: str = "completed",
    output: list[object] | None = None,
    incomplete_reason: str | None = None,
) -> SimpleNamespace:
    """Build the small ParsedResponse surface consumed by the adapter."""

    incomplete_details = (
        SimpleNamespace(reason=incomplete_reason) if incomplete_reason is not None else None
    )
    return SimpleNamespace(
        output_parsed=output_parsed,
        status=status,
        output=output or [],
        incomplete_details=incomplete_details,
        _request_id="req_test",
    )


class FakeResponses:
    """Minimal Responses API test double."""

    def __init__(self, outputs: Iterator[object]) -> None:
        self._outputs = outputs
        self.calls: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        output = next(self._outputs)
        if isinstance(output, Exception):
            raise output
        return cast(SimpleNamespace, output)


class FakeOpenAIClient:
    """OpenAI client double exposing the used Responses and lifecycle surface."""

    def __init__(self, *outputs: object) -> None:
        self.responses = FakeResponses(iter(outputs))
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1


def build_openai_provider(*outputs: object) -> tuple[OpenAIProvider, FakeOpenAIClient]:
    client = FakeOpenAIClient(*outputs)
    provider = OpenAIProvider(
        api_key="test-key",
        model="test-model",
        timeout_seconds=5,
        max_retries=0,
        client=cast(OpenAI, client),
    )
    return provider, client


def api_response(status_code: int) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"x-request-id": "req_error"},
        request=httpx.Request("POST", "https://api.openai.com"),
    )


def test_mock_provider_implements_contract_and_uses_local_tools(
    sample_resume: str,
    sample_job: str,
) -> None:
    provider = MockProvider()

    profile = provider.extract_resume_profile(sample_resume)
    job = provider.extract_job_requirements(sample_job)
    email = provider.generate_recruiter_email(
        profile,
        job,
        FitCategory.STRONG_FIT,
        ["Python", "Kafka"],
    )
    metadata = provider.metadata_for(LLMOperation.RESUME_EXTRACTION)

    assert isinstance(provider, LLMProvider)
    assert provider.name == "mock"
    assert profile.years_of_experience == 9
    assert job.company == "Acme Cloud"
    assert "Python, Kafka" in email
    assert metadata.model == "deterministic-local-v1"
    assert metadata.prompt_version == "not-applicable"
    provider.close()


@pytest.mark.parametrize(
    ("provider_name", "api_key"),
    [
        ("auto", None),
        ("auto", SecretStr("   ")),
        ("mock", None),
        ("mock", SecretStr("test-key")),
    ],
)
def test_provider_factory_uses_mock_for_auto_without_key_or_explicit_mock(
    provider_name: str,
    api_key: SecretStr | None,
) -> None:
    settings = Settings(llm_provider=provider_name, openai_api_key=api_key)

    assert isinstance(create_llm_provider(settings), MockProvider)


@pytest.mark.parametrize("api_key", [None, SecretStr("   ")])
def test_provider_factory_rejects_explicit_openai_without_key(
    api_key: SecretStr | None,
) -> None:
    settings = Settings(llm_provider="openai", openai_api_key=api_key)

    with pytest.raises(
        LLMProviderConfigurationError,
        match="OPENAI_API_KEY is required",
    ):
        create_llm_provider(settings)


@pytest.mark.parametrize("provider_name", ["auto", "openai"])
def test_provider_factory_creates_configured_openai_provider(
    provider_name: str,
) -> None:
    settings = Settings(
        llm_provider=provider_name,
        openai_api_key=SecretStr(" test-key "),
        openai_model="configured-model",
        openai_timeout_seconds=7,
        openai_max_retries=1,
    )

    provider = create_llm_provider(settings)

    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "openai"
    assert provider.model == "configured-model"
    provider.close()


def test_openai_provider_forwards_client_timeout_and_retry_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    fake_client = FakeOpenAIClient()

    def build_client(**kwargs: object) -> FakeOpenAIClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(
        "job_search_assistant.llm.openai_provider.OpenAI",
        build_client,
    )

    provider = OpenAIProvider(
        api_key="secret",
        model="test-model",
        timeout_seconds=12,
        max_retries=3,
    )

    assert captured == {
        "api_key": "secret",
        "timeout": 12,
        "max_retries": 3,
    }
    provider.close()
    assert fake_client.close_calls == 1


def test_openai_provider_uses_structured_outputs_and_versioned_metadata() -> None:
    resume_output = ResumeProfileExtraction(
        skills=["Python", "Kafka"],
        years_of_experience=8,
        target_roles=["Platform Engineer"],
        location_preferences=["Remote"],
        work_authorization="Authorized to work in the US",
        summary="Platform engineering background.",
    )
    job_output = JobRequirementsExtraction(
        title="Senior Platform Engineer",
        company="Example Cloud",
        required_skills=["Python", "Kafka"],
        preferred_skills=["Kubernetes"],
        minimum_years_experience=5,
        location="Remote",
        work_authorization_requirement="US work authorization required",
        summary="Build distributed cloud systems.",
    )
    email_output = RecruiterEmailDraft(
        subject="Senior Platform Engineer",
        body="Hello,\n\nI am interested in this role.\n\nBest regards,\nCandidate",
    )
    provider, client = build_openai_provider(
        parsed_response(resume_output),
        parsed_response(job_output),
        parsed_response(email_output),
    )

    profile = provider.extract_resume_profile("untrusted resume")
    job = provider.extract_job_requirements("untrusted job description")
    email = provider.generate_recruiter_email(
        profile,
        job,
        FitCategory.STRONG_FIT,
        ["Python", "Kafka"],
    )

    assert profile == resume_output.to_domain()
    assert job == job_output.to_domain()
    assert email == email_output.render()
    assert [call["text_format"] for call in client.responses.calls] == [
        ResumeProfileExtraction,
        JobRequirementsExtraction,
        RecruiterEmailDraft,
    ]
    assert all(call["model"] == "test-model" for call in client.responses.calls)
    assert all(call["store"] is False for call in client.responses.calls)
    assert "untrusted resume" in cast(str, client.responses.calls[0]["input"])
    assert "Validated matched skills" in cast(str, client.responses.calls[2]["input"])
    assert (
        provider.metadata_for(LLMOperation.RESUME_EXTRACTION).prompt_version
        == RESUME_EXTRACTION_PROMPT_VERSION
    )
    assert (
        provider.metadata_for(LLMOperation.JOB_EXTRACTION).prompt_version
        == JOB_EXTRACTION_PROMPT_VERSION
    )
    assert (
        provider.metadata_for(LLMOperation.RECRUITER_EMAIL).prompt_version
        == RECRUITER_EMAIL_PROMPT_VERSION
    )


def test_openai_provider_rejects_model_refusal() -> None:
    refusal = SimpleNamespace(type="refusal", refusal="I cannot process this input.")
    message = SimpleNamespace(type="message", content=[refusal])
    provider, _client = build_openai_provider(
        parsed_response(None, output=[message]),
    )

    with pytest.raises(LLMProviderRefusalError, match="resume_extraction") as raised:
        provider.extract_resume_profile("resume")

    assert raised.value.request_id == "req_test"
    assert "I cannot process this input" not in str(raised.value)


def test_openai_provider_rejects_incomplete_response() -> None:
    provider, _client = build_openai_provider(
        parsed_response(
            None,
            status="incomplete",
            incomplete_reason="max_output_tokens",
        )
    )

    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        provider.extract_resume_profile("resume")

    assert raised.value.response_kind == "incomplete"
    assert "max_output_tokens" in str(raised.value)


@pytest.mark.parametrize("status", ["failed", "cancelled", "queued"])
def test_openai_provider_rejects_non_completed_response(status: str) -> None:
    provider, _client = build_openai_provider(parsed_response(None, status=status))

    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        provider.extract_resume_profile("resume")

    assert raised.value.response_kind == "failed"


def test_openai_provider_rejects_missing_structured_output() -> None:
    provider, _client = build_openai_provider(parsed_response(None))

    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        provider.extract_resume_profile("resume")

    assert raised.value.response_kind == "parse_failure"


@pytest.mark.parametrize(
    ("error", "expected_type", "retryable"),
    [
        (
            openai.AuthenticationError(
                "authentication failed",
                response=api_response(401),
                body=None,
            ),
            LLMProviderAuthenticationError,
            False,
        ),
        (
            openai.PermissionDeniedError(
                "permission denied",
                response=api_response(403),
                body=None,
            ),
            LLMProviderAuthenticationError,
            False,
        ),
        (
            openai.RateLimitError(
                "rate limited",
                response=api_response(429),
                body=None,
            ),
            LLMProviderRateLimitError,
            True,
        ),
        (
            openai.APITimeoutError(request=httpx.Request("POST", "https://api.openai.com")),
            LLMProviderTimeoutError,
            True,
        ),
        (
            openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com")),
            LLMProviderTransientError,
            True,
        ),
        (
            openai.InternalServerError(
                "server failure",
                response=api_response(500),
                body=None,
            ),
            LLMProviderTransientError,
            True,
        ),
        (
            openai.ConflictError(
                "conflict",
                response=api_response(409),
                body=None,
            ),
            LLMProviderTransientError,
            True,
        ),
        (
            openai.BadRequestError(
                "bad request",
                response=api_response(400),
                body=None,
            ),
            LLMProviderConfigurationError,
            False,
        ),
        (
            openai.APIError(
                "provider failure",
                request=httpx.Request("POST", "https://api.openai.com"),
                body=None,
            ),
            LLMProviderInvalidResponseError,
            False,
        ),
        (
            openai.APIResponseValidationError(
                api_response(200),
                body={"unexpected": "shape"},
            ),
            LLMProviderInvalidResponseError,
            False,
        ),
        (
            openai.ContentFilterFinishReasonError(),
            LLMProviderInvalidResponseError,
            False,
        ),
    ],
)
def test_openai_provider_maps_sdk_errors(
    error: Exception,
    expected_type: type[LLMProviderError],
    retryable: bool,
) -> None:
    provider, _client = build_openai_provider(error)

    with pytest.raises(expected_type) as raised:
        provider.extract_job_requirements("job description")

    assert raised.value.retryable is retryable


def test_openai_provider_maps_pydantic_parse_failure() -> None:
    with pytest.raises(ValidationError) as caught:
        ResumeProfileExtraction.model_validate({})

    provider, _client = build_openai_provider(caught.value)

    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        provider.extract_resume_profile("resume")

    assert raised.value.response_kind == "parse_failure"


def test_openai_provider_maps_unexpected_api_status() -> None:
    provider, _client = build_openai_provider(
        openai.APIStatusError(
            "unexpected",
            response=api_response(418),
            body=None,
        )
    )

    with pytest.raises(LLMProviderInvalidResponseError) as raised:
        provider.extract_job_requirements("job description")

    assert raised.value.response_kind == "provider_error"
    assert raised.value.request_id == "req_error"
