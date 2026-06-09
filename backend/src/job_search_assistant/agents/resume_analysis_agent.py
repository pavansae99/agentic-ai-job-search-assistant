"""Resume extraction agent."""

from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.tools.resume_parser_tool import ResumeParserTool


class ResumeAnalysisAgent:
    """Convert unstructured resume text into a candidate profile."""

    def __init__(self, resume_parser: ResumeParserTool | None = None) -> None:
        self._resume_parser = resume_parser or ResumeParserTool()

    def run(self, raw_resume_text: str) -> CandidateProfile:
        """Execute the resume parser tool."""

        return self._resume_parser.parse(raw_resume_text)
