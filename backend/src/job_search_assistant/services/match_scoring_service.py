"""Deterministic and explainable resume-to-job scoring."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import ScoreBreakdown

WEIGHTS = {
    "skills": 0.50,
    "experience": 0.20,
    "location": 0.15,
    "authorization": 0.15,
}


class MatchScoringService:
    """Calculate weighted fit scores from structured profile and job facts."""

    def score(self, profile: CandidateProfile, job: ParsedJob) -> ScoreBreakdown:
        """Return component scores, weights, explanations, and a final score."""

        skill_score, skill_explanation = self._score_skills(profile, job)
        experience_score, experience_explanation = self._score_experience(profile, job)
        location_score, location_explanation = self._score_location(profile, job)
        authorization_score, authorization_explanation = self._score_authorization(profile, job)
        final_score = round(
            skill_score * WEIGHTS["skills"]
            + experience_score * WEIGHTS["experience"]
            + location_score * WEIGHTS["location"]
            + authorization_score * WEIGHTS["authorization"],
            2,
        )
        return ScoreBreakdown(
            skill_score=skill_score,
            experience_score=experience_score,
            location_score=location_score,
            authorization_score=authorization_score,
            final_score=final_score,
            weights=WEIGHTS,
            explanations={
                "skills": skill_explanation,
                "experience": experience_explanation,
                "location": location_explanation,
                "authorization": authorization_explanation,
            },
        )

    @staticmethod
    def missing_keywords(profile: CandidateProfile, job: ParsedJob) -> list[str]:
        """Return required job skills absent from the profile."""

        candidate_skills = {skill.casefold() for skill in profile.skills}
        return [skill for skill in job.required_skills if skill.casefold() not in candidate_skills]

    @staticmethod
    def _score_skills(
        profile: CandidateProfile,
        job: ParsedJob,
    ) -> tuple[float, str]:
        required = {skill.casefold() for skill in job.required_skills}
        candidate = {skill.casefold() for skill in profile.skills}
        if not required:
            return 100.0, "No explicit required skills were detected."
        matched = required & candidate
        score = round(len(matched) / len(required) * 100, 2)
        return score, f"Matched {len(matched)} of {len(required)} required skills."

    @staticmethod
    def _score_experience(
        profile: CandidateProfile,
        job: ParsedJob,
    ) -> tuple[float, str]:
        required = job.minimum_years_experience
        actual = profile.years_of_experience
        if required <= 0:
            return 100.0, "No minimum experience requirement was detected."
        score = round(min(actual / required, 1.0) * 100, 2)
        return score, f"Candidate has {actual:g} years against a {required:g}-year minimum."

    @staticmethod
    def _score_location(
        profile: CandidateProfile,
        job: ParsedJob,
    ) -> tuple[float, str]:
        job_location = job.location.casefold()
        preferences = [location.casefold() for location in profile.location_preferences]
        if job_location in {"not specified", ""}:
            return 100.0, "The job does not specify a location constraint."
        if not preferences:
            return 75.0, "Candidate location preference is unknown."
        if "remote" in job_location and any("remote" in location for location in preferences):
            return 100.0, "Both candidate and job support remote work."
        if any(
            preference in job_location or job_location in preference for preference in preferences
        ):
            return 100.0, "Job location matches a candidate preference."
        if "hybrid" in job_location:
            return 60.0, "Hybrid location requires candidate confirmation."
        return 25.0, "Job location does not match stated candidate preferences."

    @staticmethod
    def _score_authorization(
        profile: CandidateProfile,
        job: ParsedJob,
    ) -> tuple[float, str]:
        candidate = profile.work_authorization.casefold()
        requirement = job.work_authorization_requirement.casefold()
        if requirement == "not specified":
            return 100.0, "The job does not state an authorization constraint."
        if "sponsorship available" in requirement:
            return 100.0, "The employer indicates sponsorship is available."
        if "requires visa sponsorship" in candidate and (
            "unavailable" in requirement or "required" in requirement
        ):
            return 0.0, "Candidate needs sponsorship, but the role cannot provide it."
        if "not specified" in candidate:
            return 50.0, "Candidate work authorization must be confirmed."
        return 100.0, "Candidate authorization appears compatible with the role."
