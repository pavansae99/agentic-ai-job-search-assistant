"""Job description parsing agent."""

from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.tools.job_parser_tool import JobParserTool


class JobAnalysisAgent:
    """Convert an unstructured job description into requirements."""

    def __init__(self, job_parser: JobParserTool | None = None) -> None:
        self._job_parser = job_parser or JobParserTool()

    def run(self, raw_job_description: str) -> ParsedJob:
        """Execute the job parser tool."""

        return self._job_parser.parse(raw_job_description)
