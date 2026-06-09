"""Health endpoint integration test."""

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "agentic-ai-job-search-assistant",
        "version": "0.1.0",
    }
