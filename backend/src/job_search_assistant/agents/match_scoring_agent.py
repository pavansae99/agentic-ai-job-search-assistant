"""Resume-to-job scoring agent."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import ScoreBreakdown
from job_search_assistant.services.match_scoring_service import MatchScoringService


class MatchScoringAgent:
    """Use the scoring toolchain to produce an explainable match."""

    def __init__(self, match_scoring_service: MatchScoringService | None = None) -> None:
        self._match_scoring_service = match_scoring_service or MatchScoringService()

    def run(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
    ) -> tuple[ScoreBreakdown, list[str]]:
        """Return score details and missing required keywords."""

        return (
            self._match_scoring_service.score(profile, job),
            self._match_scoring_service.missing_keywords(profile, job),
        )
