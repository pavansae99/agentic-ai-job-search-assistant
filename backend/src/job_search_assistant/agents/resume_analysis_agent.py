"""Resume extraction agent."""

from job_search_assistant.llm.provider import LLMProvider, create_llm_provider
from job_search_assistant.llm.schemas import LLMOperation, LLMProviderMetadata
from job_search_assistant.schemas.profile import CandidateProfile


class ResumeAnalysisAgent:
    """Convert unstructured resume text into a candidate profile."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm_provider = llm_provider if llm_provider is not None else create_llm_provider()

    @property
    def provider_name(self) -> str:
        """Return the provider used by this agent."""

        return self._llm_provider.name

    @property
    def provider_metadata(self) -> LLMProviderMetadata:
        """Return provenance for resume extraction traces."""

        return self._llm_provider.metadata_for(LLMOperation.RESUME_EXTRACTION)

    def run(self, raw_resume_text: str) -> CandidateProfile:
        """Extract a candidate profile through the configured provider."""

        return self._llm_provider.extract_resume_profile(raw_resume_text)
