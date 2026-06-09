"""SQLite-backed application tracker endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from job_search_assistant.database.session import get_db
from job_search_assistant.repositories.application_repository import ApplicationRepository
from job_search_assistant.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)
from job_search_assistant.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["applications"])
DatabaseSession = Annotated[Session, Depends(get_db)]


def application_service(session: DatabaseSession) -> ApplicationService:
    """Construct a request-scoped application service."""

    return ApplicationService(ApplicationRepository(session))


ApplicationServiceDependency = Annotated[
    ApplicationService,
    Depends(application_service),
]


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    service: ApplicationServiceDependency,
) -> ApplicationRead:
    """Track a new job application."""

    return service.create(payload)


@router.get("", response_model=list[ApplicationRead])
def list_applications(service: ApplicationServiceDependency) -> list[ApplicationRead]:
    """List all tracked applications."""

    return service.list_all()


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    service: ApplicationServiceDependency,
) -> ApplicationRead:
    """Update application status or notes."""

    return service.update(application_id, payload)
