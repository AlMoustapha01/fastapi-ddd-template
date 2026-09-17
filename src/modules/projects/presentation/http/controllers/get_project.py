"""GET /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
)
from modules.projects.presentation.http.schemas import ProjectResponse


def create_get_project_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Get a project",
    )
    @inject
    async def get_project(
        project_id: UUID, query: FromDishka[GetProjectByIdQuery]
    ) -> ProjectResponse:
        project = await query.execute(GetProjectByIdRequest(project_id=project_id))
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
