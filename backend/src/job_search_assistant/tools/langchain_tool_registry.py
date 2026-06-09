"""LangChain adapters for model-driven tool calling."""

from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

from job_search_assistant.tools.job_parser_tool import JobParserTool
from job_search_assistant.tools.resume_parser_tool import ResumeParserTool


class ResumeParserInput(BaseModel):
    """Arguments accepted by the resume parser tool."""

    raw_resume_text: str = Field(min_length=20)


class JobParserInput(BaseModel):
    """Arguments accepted by the job parser tool."""

    raw_job_description: str = Field(min_length=20)


def _parse_resume(raw_resume_text: str) -> dict[str, Any]:
    return ResumeParserTool().parse(raw_resume_text).model_dump()


def _parse_job(raw_job_description: str) -> dict[str, Any]:
    return JobParserTool().parse(raw_job_description).model_dump()


def build_tool_registry() -> list[BaseTool]:
    """Return tools that can be bound to a LangChain chat model."""

    return [
        StructuredTool.from_function(
            func=_parse_resume,
            name="parse_candidate_resume",
            description="Extract structured candidate facts from raw resume text.",
            args_schema=ResumeParserInput,
        ),
        StructuredTool.from_function(
            func=_parse_job,
            name="parse_job_description",
            description="Extract structured requirements from a raw job description.",
            args_schema=JobParserInput,
        ),
    ]
