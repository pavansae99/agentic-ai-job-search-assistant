"""FastAPI application composition root."""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from job_search_assistant.api.routes import applications, health, jobs, profiles
from job_search_assistant.container import ApplicationContainer, build_application_container
from job_search_assistant.core.exceptions import ApplicationNotFoundError
from job_search_assistant.core.logging_config import configure_logging
from job_search_assistant.core.settings import Settings, get_settings
from job_search_assistant.database.base import Base
from job_search_assistant.database.session import engine
from job_search_assistant.llm.provider import LLMProviderError
from job_search_assistant.models import Application  # noqa: F401

logger = logging.getLogger(__name__)
ContainerFactory = Callable[[Settings], ApplicationContainer]


def create_app(
    app_settings: Settings | None = None,
    container_factory: ContainerFactory = build_application_container,
) -> FastAPI:
    """Create and configure the API application."""

    settings = app_settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        """Initialize shared resources and close them during shutdown."""

        Base.metadata.create_all(bind=engine)
        container = container_factory(settings)
        application.state.container = container
        try:
            yield
        finally:
            container.close()

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

    @application.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(
        _request: Request,
        exc: LLMProviderError,
    ) -> JSONResponse:
        logger.error(
            "LLM provider request failed category=%s retryable=%s request_id=%s",
            exc.error_code,
            exc.retryable,
            exc.request_id,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "The AI provider is temporarily unavailable."},
        )

    return application


app = create_app()
