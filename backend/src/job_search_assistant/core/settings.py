"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with development-safe defaults."""

    app_name: str = "Agentic AI Job Search Assistant"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./job_search.db"
    llm_provider: Literal["auto", "mock", "openai"] = "auto"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.4-mini"
    openai_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    openai_max_retries: int = Field(default=2, ge=0, le=10)
    # Reserved for Phase 2 end-to-end cancellation; SDK timeouts remain per request.
    llm_workflow_deadline_seconds: float | None = Field(default=None, gt=0, le=900)

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
