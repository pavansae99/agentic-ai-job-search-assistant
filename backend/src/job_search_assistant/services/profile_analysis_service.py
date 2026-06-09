"""Resume analysis use cases."""

from job_search_assistant.agents.career_coach_agent import CareerCoachAgent
from job_search_assistant.agents.resume_analysis_agent import ResumeAnalysisAgent
from job_search_assistant.llm.provider import LLMProvider, create_llm_provider
from job_search_assistant.schemas.profile import ProfileAnalysisResponse


class ProfileAnalysisService:
    """Coordinate profile extraction and baseline career coaching."""

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        resume_analysis_agent: ResumeAnalysisAgent | None = None,
        career_coach_agent: CareerCoachAgent | None = None,
    ) -> None:
        provider = llm_provider if llm_provider is not None else create_llm_provider()
        self._resume_analysis_agent = resume_analysis_agent or ResumeAnalysisAgent(provider)
        self._career_coach_agent = career_coach_agent or CareerCoachAgent()

    def analyze(self, raw_resume_text: str) -> ProfileAnalysisResponse:
        """Analyze a resume and return structured facts and suggestions."""

        profile = self._resume_analysis_agent.run(raw_resume_text)
        suggestions = self._career_coach_agent.review_profile(profile)
        metadata = self._resume_analysis_agent.provider_metadata.trace_fragment()
        return ProfileAnalysisResponse(
            profile=profile,
            career_suggestions=suggestions,
            reasoning_trace=[
                f"ResumeAnalysisAgent extracted normalized candidate facts with {metadata}.",
                "CareerCoachAgent reviewed profile completeness.",
            ],
        )
