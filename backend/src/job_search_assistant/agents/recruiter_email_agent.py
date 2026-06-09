"""Recruiter email agent."""

from job_search_assistant.llm.provider import LLMProvider, create_llm_provider
from job_search_assistant.llm.schemas import LLMOperation, LLMProviderMetadata
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory


class RecruiterEmailAgent:
    """Generate grounded recruiter outreach from workflow state."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self._llm_provider = llm_provider if llm_provider is not None else create_llm_provider()

    @property
    def provider_name(self) -> str:
        """Return the provider used by this agent."""

        return self._llm_provider.name

    @property
    def provider_metadata(self) -> LLMProviderMetadata:
        """Return provenance for recruiter email traces."""

        return self._llm_provider.metadata_for(LLMOperation.RECRUITER_EMAIL)

    def run(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        missing_keywords: list[str],
    ) -> str:
        """Generate an email using only skills present in the profile."""

        missing = {skill.casefold() for skill in missing_keywords}
        matched = [skill for skill in job.required_skills if skill.casefold() not in missing]
        return self._llm_provider.generate_recruiter_email(profile, job, ranking, matched)
