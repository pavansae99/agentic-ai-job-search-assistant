"""Application tracker endpoint integration tests."""

from fastapi.testclient import TestClient


def test_application_lifecycle(client: TestClient) -> None:
    create_response = client.post(
        "/api/applications",
        json={
            "company": "Acme Cloud",
            "title": "Senior Backend Engineer",
            "location": "Remote",
            "job_url": "https://example.com/jobs/backend",
            "match_score": 94.5,
            "notes": "High-priority role",
        },
    )
    assert create_response.status_code == 201
    application_id = create_response.json()["id"]

    list_response = client.get("/api/applications")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/applications/{application_id}",
        json={"status": "applied", "notes": "Applied with referral"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "applied"
    assert update_response.json()["notes"] == "Applied with referral"


def test_application_update_returns_404(client: TestClient) -> None:
    response = client.patch("/api/applications/404", json={"status": "rejected"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Application 404 was not found."


def test_application_rejects_empty_patch(client: TestClient) -> None:
    response = client.patch("/api/applications/1", json={})

    assert response.status_code == 422


def test_application_rejects_null_required_field(client: TestClient) -> None:
    response = client.patch("/api/applications/1", json={"status": None})

    assert response.status_code == 422
