"""Application-scoped service and provider composition."""

from dataclasses import dataclass

from job_search_assistant.core.settings import Settings
from job_search_assistant.llm.provider import LLMProvider, create_llm_provider
from job_search_assistant.services.job_analysis_service import JobAnalysisService
from job_search_assistant.services.profile_analysis_service import ProfileAnalysisService


@dataclass(frozen=True)
class ApplicationContainer:
    """Resources shared across API requests."""

    llm_provider: LLMProvider
    profile_analysis_service: ProfileAnalysisService
    job_analysis_service: JobAnalysisService

    @classmethod
    def from_provider(cls, provider: LLMProvider) -> "ApplicationContainer":
        """Build services around one provider and one compiled workflow."""

        return cls(
            llm_provider=provider,
            profile_analysis_service=ProfileAnalysisService(llm_provider=provider),
            job_analysis_service=JobAnalysisService(llm_provider=provider),
        )

    def close(self) -> None:
        """Release application-scoped resources."""

        self.llm_provider.close()


def build_application_container(settings: Settings) -> ApplicationContainer:
    """Create the application container from validated settings."""

    return ApplicationContainer.from_provider(create_llm_provider(settings))
