"""FastAPI dependencies backed by the application-scoped container."""

from typing import Annotated, cast

from fastapi import Depends, Request

from job_search_assistant.container import ApplicationContainer
from job_search_assistant.services.job_analysis_service import JobAnalysisService
from job_search_assistant.services.profile_analysis_service import ProfileAnalysisService


def get_application_container(request: Request) -> ApplicationContainer:
    """Return the container initialized during application startup."""

    return cast(ApplicationContainer, request.app.state.container)


ContainerDependency = Annotated[
    ApplicationContainer,
    Depends(get_application_container),
]


def get_profile_analysis_service(
    container: ContainerDependency,
) -> ProfileAnalysisService:
    """Return the shared profile analysis service."""

    return container.profile_analysis_service


def get_job_analysis_service(container: ContainerDependency) -> JobAnalysisService:
    """Return the shared job analysis service."""

    return container.job_analysis_service


ProfileAnalysisServiceDependency = Annotated[
    ProfileAnalysisService,
    Depends(get_profile_analysis_service),
]
JobAnalysisServiceDependency = Annotated[
    JobAnalysisService,
    Depends(get_job_analysis_service),
]
