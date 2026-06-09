"""Job analysis and matching use cases."""

from job_search_assistant.agents.job_analysis_agent import JobAnalysisAgent
from job_search_assistant.schemas.job import JobAnalysisResponse, JobMatchResponse
from job_search_assistant.workflows.job_match_workflow import JobMatchWorkflow


class JobAnalysisService:
    """Coordinate standalone parsing and end-to-end matching."""

    def __init__(
        self,
        job_analysis_agent: JobAnalysisAgent | None = None,
        job_match_workflow: JobMatchWorkflow | None = None,
    ) -> None:
        self._job_analysis_agent = job_analysis_agent or JobAnalysisAgent()
        self._job_match_workflow = job_match_workflow or JobMatchWorkflow()

    def analyze(self, raw_job_description: str) -> JobAnalysisResponse:
        """Parse one job description."""

        job = self._job_analysis_agent.run(raw_job_description)
        return JobAnalysisResponse(
            job=job,
            reasoning_trace=["JobAnalysisAgent extracted normalized job requirements."],
        )

    def match(self, raw_resume_text: str, raw_job_description: str) -> JobMatchResponse:
        """Run the complete LangGraph workflow."""

        return self._job_match_workflow.run(raw_resume_text, raw_job_description)
