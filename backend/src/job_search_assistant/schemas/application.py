"""Application tracker request and response schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ApplicationStatus(StrEnum):
    """Supported application pipeline states."""

    SAVED = "saved"
    APPLIED = "applied"
    RECRUITER_CONTACTED = "recruiter_contacted"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"


class ApplicationCreate(BaseModel):
    """Fields accepted when tracking a new application."""

    company: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    job_url: HttpUrl | None = None
    status: ApplicationStatus = ApplicationStatus.SAVED
    match_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=10_000)


class ApplicationUpdate(BaseModel):
    """Fields that can be changed on an application."""

    company: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    job_url: HttpUrl | None = None
    status: ApplicationStatus | None = None
    match_score: float | None = Field(default=None, ge=0, le=100)
    notes: str | None = Field(default=None, max_length=10_000)

    @model_validator(mode="after")
    def reject_empty_update(self) -> "ApplicationUpdate":
        """Require an update and protect database-required fields from null."""

        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied.")
        required_fields = {"company", "title", "status"}
        null_required_fields = [
            field
            for field in required_fields & self.model_fields_set
            if getattr(self, field) is None
        ]
        if null_required_fields:
            fields = ", ".join(sorted(null_required_fields))
            raise ValueError(f"These fields cannot be null: {fields}.")
        return self


class ApplicationRead(BaseModel):
    """Persisted application returned by the API."""

    id: int
    company: str
    title: str
    location: str | None
    job_url: str | None
    status: ApplicationStatus
    match_score: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
