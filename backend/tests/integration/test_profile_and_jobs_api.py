"""Profile and job endpoint integration tests."""

from fastapi.testclient import TestClient


def test_profile_analysis_endpoint(client: TestClient, sample_resume: str) -> None:
    response = client.post(
        "/api/profile/analyze",
        json={"raw_resume_text": sample_resume},
    )

    assert response.status_code == 200
    assert response.json()["profile"]["years_of_experience"] == 9
    assert "Python" in response.json()["profile"]["skills"]


def test_job_analysis_and_match_endpoints(
    client: TestClient,
    sample_resume: str,
    sample_job: str,
) -> None:
    analysis_response = client.post(
        "/api/jobs/analyze",
        json={"raw_job_description": sample_job},
    )
    match_response = client.post(
        "/api/jobs/match",
        json={
            "raw_resume_text": sample_resume,
            "raw_job_description": sample_job,
        },
    )

    assert analysis_response.status_code == 200
    assert analysis_response.json()["job"]["company"] == "Acme Cloud"
    assert match_response.status_code == 200
    assert match_response.json()["ranking"] == "Strong Fit"
    assert match_response.json()["scoring"]["final_score"] >= 85
    assert match_response.json()["recruiter_email"].startswith("Subject:")


def test_analysis_rejects_short_text(client: TestClient) -> None:
    response = client.post("/api/profile/analyze", json={"raw_resume_text": "too short"})

    assert response.status_code == 422
