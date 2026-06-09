"""Repository for application tracker persistence."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from job_search_assistant.models.application import Application


class ApplicationRepository:
    """Encapsulate SQLAlchemy queries for application records."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, values: Mapping[str, Any]) -> Application:
        """Persist and return an application."""

        application = Application(**values)
        self._session.add(application)
        self._session.commit()
        self._session.refresh(application)
        return application

    def list_all(self) -> list[Application]:
        """Return applications newest first."""

        statement = select(Application).order_by(Application.created_at.desc())
        return list(self._session.scalars(statement))

    def get(self, application_id: int) -> Application | None:
        """Return one application by identifier."""

        return self._session.get(Application, application_id)

    def update(
        self,
        application: Application,
        values: Mapping[str, Any],
    ) -> Application:
        """Apply validated field updates and persist them."""

        for field, value in values.items():
            setattr(application, field, value)
        self._session.add(application)
        self._session.commit()
        self._session.refresh(application)
        return application
