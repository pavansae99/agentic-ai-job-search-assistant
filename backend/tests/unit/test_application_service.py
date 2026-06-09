"""Tests for the application repository/service boundary."""

import pytest
from sqlalchemy.orm import Session

from job_search_assistant.core.exceptions import ApplicationNotFoundError
from job_search_assistant.repositories.application_repository import ApplicationRepository
from job_search_assistant.schemas.application import (
    ApplicationCreate,
    ApplicationStatus,
    ApplicationUpdate,
)
from job_search_assistant.services.application_service import ApplicationService


def test_application_service_create_list_and_update(db_session: Session) -> None:
    service = ApplicationService(ApplicationRepository(db_session))
    created = service.create(
        ApplicationCreate(
            company="Acme",
            title="Senior Engineer",
            job_url="https://example.com/jobs/1",
            match_score=91,
        )
    )

    assert created.id > 0
    assert created.status is ApplicationStatus.SAVED
    assert service.list_all()[0].company == "Acme"

    updated = service.update(
        created.id,
        ApplicationUpdate(status=ApplicationStatus.APPLIED, notes="Applied via referral"),
    )

    assert updated.status is ApplicationStatus.APPLIED
    assert updated.notes == "Applied via referral"


def test_application_service_raises_for_unknown_id(db_session: Session) -> None:
    service = ApplicationService(ApplicationRepository(db_session))

    with pytest.raises(ApplicationNotFoundError, match="999"):
        service.update(999, ApplicationUpdate(status=ApplicationStatus.REJECTED))
