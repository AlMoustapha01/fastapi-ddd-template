"""PATCH /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    UpdateProjectCommand,
    UpdateProjectRequest,
)
from modules.projects.presentation.http.schemas import (
    ProjectResponse,
    UpdateProjectBody,
)


def create_update_project_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Update a project",
    )
    @inject
    async def update_project(
        project_id: UUID,
        body: UpdateProjectBody,
        command: FromDishka[UpdateProjectCommand],
    ) -> ProjectResponse:
        project = await command.execute(
            UpdateProjectRequest(
                project_id=project_id, name=body.name, description=body.description
            )
        )
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
