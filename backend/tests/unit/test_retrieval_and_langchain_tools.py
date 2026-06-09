"""Tests for retrieval behavior and LangChain tool adapters."""

import pytest

from job_search_assistant.tools.langchain_tool_registry import build_tool_registry
from job_search_assistant.tools.vector_search_tool import VectorSearchTool


def test_vector_search_ranks_relevant_documents() -> None:
    store = VectorSearchTool()
    relevant_id = store.add_document(
        "Python Kafka distributed systems",
        {"kind": "resume"},
        document_id="resume-1",
    )
    store.add_document("React design systems", document_id="resume-2")

    results = store.search("Python distributed systems", limit=1)

    assert relevant_id == "resume-1"
    assert results[0].document_id == "resume-1"
    assert results[0].score > 0
    assert results[0].metadata == {"kind": "resume"}


def test_vector_search_validates_inputs() -> None:
    store = VectorSearchTool()

    with pytest.raises(ValueError, match="empty"):
        store.add_document(" ")
    with pytest.raises(ValueError, match="at least 1"):
        store.search("python", limit=0)


def test_langchain_registry_exposes_typed_parser_tools(
    sample_resume: str,
    sample_job: str,
) -> None:
    tools = {tool.name: tool for tool in build_tool_registry()}

    profile = tools["parse_candidate_resume"].invoke({"raw_resume_text": sample_resume})
    job = tools["parse_job_description"].invoke({"raw_job_description": sample_job})

    assert set(tools) == {"parse_candidate_resume", "parse_job_description"}
    assert profile["years_of_experience"] == 9
    assert "Python" in profile["skills"]
    assert job["company"] == "Acme Cloud"
