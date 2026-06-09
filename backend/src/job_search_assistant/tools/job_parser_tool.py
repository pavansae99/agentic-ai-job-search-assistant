"""Local job-description parser used by the job parser agent."""

import re

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.tools.text_extraction import (
    extract_labeled_value,
    extract_skills,
    extract_years,
)


class JobParserTool:
    """Extract normalized job requirements from a description."""

    def parse(self, raw_job_description: str) -> ParsedJob:
        """Parse title, skills, experience, location, and authorization constraints."""

        required_text, preferred_text = self._split_requirements(raw_job_description)
        required_skills = extract_skills(required_text)
        preferred_skills = [
            skill for skill in extract_skills(preferred_text) if skill not in required_skills
        ]
        all_skills = extract_skills(raw_job_description)
        if not required_skills:
            required_skills = [skill for skill in all_skills if skill not in preferred_skills]

        title = extract_labeled_value(raw_job_description, ("Job title", "Title", "Role"))
        company = extract_labeled_value(raw_job_description, ("Company", "Organization"))
        location = extract_labeled_value(
            raw_job_description,
            ("Location", "Work location"),
        )
        return ParsedJob(
            title=title or "Unknown role",
            company=company or "Unknown company",
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            minimum_years_experience=extract_years(raw_job_description),
            location=location or self._infer_location(raw_job_description),
            work_authorization_requirement=self._extract_authorization(raw_job_description),
            summary=(
                f"{title or 'Role'} requiring {len(required_skills)} core skills "
                f"and {extract_years(raw_job_description):g}+ years of experience."
            ),
        )

    @staticmethod
    def _split_requirements(text: str) -> tuple[str, str]:
        marker = re.search(
            r"^(preferred|nice to have|bonus|desired)(?:\s+qualifications|\s+skills)?\s*:?",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if marker is None:
            return text, ""
        return text[: marker.start()], text[marker.end() :]

    @staticmethod
    def _infer_location(text: str) -> str:
        if re.search(r"\bremote\b", text, re.IGNORECASE):
            return "Remote"
        if re.search(r"\bhybrid\b", text, re.IGNORECASE):
            return "Hybrid"
        return "Not specified"

    @staticmethod
    def _extract_authorization(text: str) -> str:
        lowered = text.casefold()
        if "no sponsorship" in lowered or "unable to sponsor" in lowered:
            return "US work authorization required; sponsorship unavailable"
        if "sponsorship available" in lowered or "will sponsor" in lowered:
            return "Visa sponsorship available"
        if "authorized to work" in lowered:
            return "US work authorization required"
        return "not specified"
