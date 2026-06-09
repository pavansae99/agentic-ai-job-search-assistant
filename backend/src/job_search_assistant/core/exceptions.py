"""Domain-specific exceptions translated by the API layer."""


class DomainError(Exception):
    """Base class for expected business errors."""


class ApplicationNotFoundError(DomainError):
    """Raised when an application record cannot be found."""

    def __init__(self, application_id: int) -> None:
        super().__init__(f"Application {application_id} was not found.")
        self.application_id = application_id
