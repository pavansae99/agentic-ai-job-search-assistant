"""Recruiter outreach email generation tool."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory


class EmailGeneratorTool:
    """Generate concise recruiter outreach from structured, grounded facts."""

    def generate(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        """Create an email that never invents candidate experience."""

        skill_text = ", ".join(matched_skills[:4]) or "backend engineering"
        role = profile.target_roles[0] if profile.target_roles else "software engineer"
        return (
            f"Subject: Interest in {job.title} at {job.company}\n\n"
            "Hello,\n\n"
            f"I am reaching out about the {job.title} opportunity at {job.company}. "
            f"My background as a {role} includes {profile.years_of_experience:g} years "
            f"of experience and hands-on work with {skill_text}. The role currently "
            f"looks like a {ranking.value.lower()} based on the stated requirements.\n\n"
            "I would welcome the opportunity to discuss how my experience could support "
            f"the team. Thank you for your time.\n\n"
            "Best regards,\n"
            "Candidate"
        )
