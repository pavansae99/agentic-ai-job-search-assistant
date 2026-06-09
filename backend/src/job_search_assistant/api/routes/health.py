"""Service health endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from job_search_assistant.core.settings import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Basic process health response."""

    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report API process health without touching external dependencies."""

    settings = get_settings()
    return HealthResponse(
        status="healthy",
        service="agentic-ai-job-search-assistant",
        version=settings.app_version,
    )
