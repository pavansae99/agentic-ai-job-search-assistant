"""Job analysis and matching use cases."""

from job_search_assistant.agents.job_analysis_agent import JobAnalysisAgent
from job_search_assistant.llm.provider import LLMProvider, create_llm_provider
from job_search_assistant.schemas.job import JobAnalysisResponse, JobMatchResponse
from job_search_assistant.workflows.job_match_workflow import JobMatchWorkflow


class JobAnalysisService:
    """Coordinate standalone parsing and end-to-end matching."""

    def __init__(
        self,
        llm_provider: LLMProvider | None = None,
        job_analysis_agent: JobAnalysisAgent | None = None,
        job_match_workflow: JobMatchWorkflow | None = None,
    ) -> None:
        provider = llm_provider if llm_provider is not None else create_llm_provider()
        self._job_analysis_agent = job_analysis_agent or JobAnalysisAgent(provider)
        self._job_match_workflow = job_match_workflow or JobMatchWorkflow(llm_provider=provider)

    def analyze(self, raw_job_description: str) -> JobAnalysisResponse:
        """Parse one job description."""

        job = self._job_analysis_agent.run(raw_job_description)
        metadata = self._job_analysis_agent.provider_metadata.trace_fragment()
        return JobAnalysisResponse(
            job=job,
            reasoning_trace=[
                f"JobAnalysisAgent extracted normalized job requirements with {metadata}."
            ],
        )

    def match(self, raw_resume_text: str, raw_job_description: str) -> JobMatchResponse:
        """Run the complete LangGraph workflow."""

        return self._job_match_workflow.run(raw_resume_text, raw_job_description)
