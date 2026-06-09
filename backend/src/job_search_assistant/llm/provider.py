"""LLM provider contract and runtime provider selection."""

from typing import Literal, Protocol, runtime_checkable

from job_search_assistant.core.settings import Settings, get_settings
from job_search_assistant.llm.schemas import LLMOperation, LLMProviderMetadata
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory


class LLMProviderError(RuntimeError):
    """Base error raised when an LLM provider cannot complete a request."""

    error_code = "llm_provider_error"
    retryable = False

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(message)
        self.request_id = request_id


class LLMProviderConfigurationError(LLMProviderError):
    """Raised when provider configuration cannot support the requested mode."""

    error_code = "llm_provider_configuration_error"


class LLMProviderAuthenticationError(LLMProviderError):
    """Raised when provider credentials are invalid or unauthorized."""

    error_code = "llm_provider_authentication_error"


class LLMProviderRateLimitError(LLMProviderError):
    """Raised when a provider rejects a request because of a rate limit."""

    error_code = "llm_provider_rate_limit_error"
    retryable = True


class LLMProviderTimeoutError(LLMProviderError):
    """Raised when a provider request exceeds its configured timeout."""

    error_code = "llm_provider_timeout_error"
    retryable = True


class LLMProviderTransientError(LLMProviderError):
    """Raised for retryable provider connectivity or service failures."""

    error_code = "llm_provider_transient_error"
    retryable = True


InvalidResponseKind = Literal["failed", "incomplete", "parse_failure", "provider_error"]


class LLMProviderInvalidResponseError(LLMProviderError):
    """Raised when a provider response cannot satisfy the expected contract."""

    error_code = "llm_provider_invalid_response_error"

    def __init__(
        self,
        message: str,
        *,
        response_kind: InvalidResponseKind,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, request_id=request_id)
        self.response_kind = response_kind


class LLMProviderRefusalError(LLMProviderError):
    """Raised when the model refuses to fulfill the requested operation."""

    error_code = "llm_provider_refusal_error"


@runtime_checkable
class LLMProvider(Protocol):
    """Capabilities required by AI-facing workflow agents."""

    @property
    def name(self) -> str:
        """Return a stable provider identifier for logs and traces."""

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile:
        """Extract a structured candidate profile from resume text."""

    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob:
        """Extract structured requirements from a job description."""

    def generate_recruiter_email(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        """Draft recruiter outreach grounded in validated workflow state."""

    def metadata_for(self, operation: LLMOperation) -> LLMProviderMetadata:
        """Return stable provider, model, and prompt metadata for traces."""

    def close(self) -> None:
        """Release provider-owned resources."""


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Select the configured provider and reject explicit invalid configuration."""

    resolved_settings = settings or get_settings()
    if resolved_settings.llm_provider == "mock":
        from job_search_assistant.llm.mock_provider import MockProvider

        return MockProvider()

    api_key = resolved_settings.openai_api_key
    if api_key is None or not api_key.get_secret_value().strip():
        from job_search_assistant.llm.mock_provider import MockProvider

        if resolved_settings.llm_provider == "openai":
            raise LLMProviderConfigurationError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai."
            )
        return MockProvider()

    from job_search_assistant.llm.openai_provider import OpenAIProvider

    return OpenAIProvider(
        api_key=api_key.get_secret_value().strip(),
        model=resolved_settings.openai_model,
        timeout_seconds=resolved_settings.openai_timeout_seconds,
        max_retries=resolved_settings.openai_max_retries,
    )
