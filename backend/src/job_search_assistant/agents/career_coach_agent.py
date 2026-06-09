"""Career improvement recommendation agent."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import ScoreBreakdown


class CareerCoachAgent:
    """Produce specific, grounded suggestions from structured gaps."""

    def review_profile(self, profile: CandidateProfile) -> list[str]:
        """Identify missing profile information before job matching."""

        suggestions: list[str] = []
        if not profile.skills:
            suggestions.append("Add a dedicated technical skills section with concrete tools.")
        if not profile.target_roles:
            suggestions.append("State one or two target roles near the top of the resume.")
        if not profile.location_preferences:
            suggestions.append("Clarify location and remote-work preferences.")
        if profile.work_authorization == "not specified":
            suggestions.append("Record work authorization privately for compatibility checks.")
        return suggestions or ["Profile contains the core facts needed for job matching."]

    def review_match(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        scoring: ScoreBreakdown,
        missing_keywords: list[str],
    ) -> list[str]:
        """Recommend truthful improvements for a specific application."""

        suggestions: list[str] = []
        if missing_keywords:
            suggestions.append(
                "Address these gaps only when supported by real experience: "
                + ", ".join(missing_keywords)
                + "."
            )
        if scoring.experience_score < 100:
            suggestions.append(
                "Emphasize scope, ownership, and comparable complexity to offset the "
                "experience requirement."
            )
        if scoring.location_score < 100:
            suggestions.append(f"Confirm willingness to work in the role's {job.location} model.")
        if scoring.authorization_score < 100:
            suggestions.append("Confirm work authorization before investing in the application.")
        if not suggestions:
            role = profile.target_roles[0] if profile.target_roles else "engineering"
            suggestions.append(f"Lead with quantified impact from the strongest {role} experience.")
        return suggestions
