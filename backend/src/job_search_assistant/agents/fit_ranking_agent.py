"""Fit classification agent."""

from job_search_assistant.schemas.scoring import FitCategory


class FitRankingAgent:
    """Translate a numeric match score into a recommendation band."""

    def run(self, final_score: float) -> FitCategory:
        """Classify a score using documented, stable thresholds."""

        if final_score >= 85:
            return FitCategory.STRONG_FIT
        if final_score >= 70:
            return FitCategory.GOOD_FIT
        if final_score >= 50:
            return FitCategory.WEAK_FIT
        return FitCategory.NOT_RECOMMENDED
