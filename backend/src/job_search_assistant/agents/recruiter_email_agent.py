"""Recruiter email agent."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory
from job_search_assistant.tools.email_generator_tool import EmailGeneratorTool


class RecruiterEmailAgent:
    """Generate grounded recruiter outreach from workflow state."""

    def __init__(self, email_generator: EmailGeneratorTool | None = None) -> None:
        self._email_generator = email_generator or EmailGeneratorTool()

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
        return self._email_generator.generate(profile, job, ranking, matched)
