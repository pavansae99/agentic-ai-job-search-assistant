"""Deterministic provider used for tests and API-key-free execution."""

from job_search_assistant.llm.schemas import LLMOperation, LLMProviderMetadata
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory
from job_search_assistant.tools.email_generator_tool import EmailGeneratorTool
from job_search_assistant.tools.job_parser_tool import JobParserTool
from job_search_assistant.tools.resume_parser_tool import ResumeParserTool


class MockProvider:
    """Implement the provider contract with existing deterministic tools."""

    name = "mock"

    def __init__(
        self,
        resume_parser: ResumeParserTool | None = None,
        job_parser: JobParserTool | None = None,
        email_generator: EmailGeneratorTool | None = None,
    ) -> None:
        self._resume_parser = resume_parser or ResumeParserTool()
        self._job_parser = job_parser or JobParserTool()
        self._email_generator = email_generator or EmailGeneratorTool()

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile:
        """Extract a profile with the deterministic resume parser."""

        return self._resume_parser.parse(raw_resume_text)

    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob:
        """Extract requirements with the deterministic job parser."""

        return self._job_parser.parse(raw_job_description)

    def generate_recruiter_email(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        """Generate outreach with the deterministic email template."""

        return self._email_generator.generate(profile, job, ranking, matched_skills)

    def metadata_for(self, operation: LLMOperation) -> LLMProviderMetadata:
        """Return deterministic implementation metadata for internal traces."""

        return LLMProviderMetadata(
            provider=self.name,
            model="deterministic-local-v1",
            prompt_version="not-applicable",
            operation=operation,
        )

    def close(self) -> None:
        """Release provider resources; deterministic tools own none."""
