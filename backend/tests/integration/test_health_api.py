"""Health endpoint integration test."""

from fastapi.testclient import TestClient

from job_search_assistant.llm.provider import LLMProviderError
from job_search_assistant.main import create_app


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "agentic-ai-job-search-assistant",
        "version": "0.1.0",
    }


def test_llm_provider_errors_are_returned_as_service_unavailable() -> None:
    application = create_app()

    @application.get("/_test/provider-error")
    def raise_provider_error() -> None:
        raise LLMProviderError("sensitive upstream detail")

    with TestClient(application, raise_server_exceptions=False) as test_client:
        response = test_client.get("/_test/provider-error")

    assert response.status_code == 503
    assert response.json() == {"detail": "The AI provider is temporarily unavailable."}
    assert "sensitive upstream detail" not in response.text
