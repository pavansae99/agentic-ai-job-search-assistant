"""Local resume parser used by the resume agent."""

import re

from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.tools.text_extraction import (
    ROLE_NAMES,
    extract_labeled_value,
    extract_skills,
    extract_years,
)


class ResumeParserTool:
    """Extract stable profile facts without requiring an external model."""

    def parse(self, raw_resume_text: str) -> CandidateProfile:
        """Parse resume text into a normalized candidate profile."""

        skills = extract_skills(raw_resume_text)
        roles = [role for role in ROLE_NAMES if role.casefold() in raw_resume_text.casefold()]
        preferred_role = extract_labeled_value(
            raw_resume_text,
            ("Target role", "Target roles", "Desired role"),
        )
        if preferred_role:
            roles.insert(0, preferred_role)

        locations = self._extract_locations(raw_resume_text)
        work_authorization = self._extract_authorization(raw_resume_text)
        years = extract_years(raw_resume_text)
        summary = (
            f"{years:g} years of experience; {len(skills)} recognized skills; "
            f"targeting {roles[0] if roles else 'software engineering roles'}."
        )
        return CandidateProfile(
            skills=skills,
            years_of_experience=years,
            target_roles=roles,
            location_preferences=locations,
            work_authorization=work_authorization,
            summary=summary,
        )

    @staticmethod
    def _extract_locations(text: str) -> list[str]:
        location = extract_labeled_value(
            text,
            ("Location preference", "Location preferences", "Preferred location"),
        )
        locations = re.split(r"[,;/]|\bor\b", location, flags=re.IGNORECASE) if location else []
        if re.search(r"\bremote\b", text, re.IGNORECASE):
            locations.append("Remote")
        return [value.strip() for value in locations if value.strip()]

    @staticmethod
    def _extract_authorization(text: str) -> str:
        lowered = text.casefold()
        if "u.s. citizen" in lowered or "us citizen" in lowered:
            return "US citizen"
        if "permanent resident" in lowered or "green card" in lowered:
            return "US permanent resident"
        if "no sponsorship required" in lowered or "authorized to work" in lowered:
            return "Authorized to work in the US without sponsorship"
        if "require sponsorship" in lowered or "visa sponsorship" in lowered:
            return "Requires visa sponsorship"
        return "not specified"
