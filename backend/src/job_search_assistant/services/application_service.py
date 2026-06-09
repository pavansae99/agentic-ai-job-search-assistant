"""Application tracker use cases."""

from job_search_assistant.core.exceptions import ApplicationNotFoundError
from job_search_assistant.repositories.application_repository import ApplicationRepository
from job_search_assistant.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)


class ApplicationService:
    """Validate and coordinate application persistence operations."""

    def __init__(self, repository: ApplicationRepository) -> None:
        self._repository = repository

    def create(self, payload: ApplicationCreate) -> ApplicationRead:
        """Create an application tracker record."""

        values = payload.model_dump(mode="json")
        application = self._repository.create(values)
        return ApplicationRead.model_validate(application)

    def list_all(self) -> list[ApplicationRead]:
        """List tracked applications."""

        return [
            ApplicationRead.model_validate(application)
            for application in self._repository.list_all()
        ]

    def update(
        self,
        application_id: int,
        payload: ApplicationUpdate,
    ) -> ApplicationRead:
        """Update an application or raise a domain-level not-found error."""

        application = self._repository.get(application_id)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        values = payload.model_dump(exclude_unset=True, mode="json")
        updated = self._repository.update(application, values)
        return ApplicationRead.model_validate(updated)
