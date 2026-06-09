"""FastAPI application composition root."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from job_search_assistant.api.routes import applications, health, jobs, profiles
from job_search_assistant.core.exceptions import ApplicationNotFoundError
from job_search_assistant.core.logging_config import configure_logging
from job_search_assistant.core.settings import get_settings
from job_search_assistant.database.base import Base
from job_search_assistant.database.session import engine
from job_search_assistant.models import Application  # noqa: F401

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize local persistence and release lifecycle control."""

    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Create and configure the API application."""

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Explainable multi-agent job matching and application tracking API.",
        lifespan=lifespan,
    )
    application.include_router(health.router)
    application.include_router(profiles.router, prefix=settings.api_prefix)
    application.include_router(jobs.router, prefix=settings.api_prefix)
    application.include_router(applications.router, prefix=settings.api_prefix)

    @application.exception_handler(ApplicationNotFoundError)
    async def application_not_found_handler(
        _request: Request,
        exc: ApplicationNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    return application


app = create_app()
