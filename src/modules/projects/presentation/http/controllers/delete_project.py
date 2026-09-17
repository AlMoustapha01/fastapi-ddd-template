"""DELETE /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    DeleteProjectCommand,
    DeleteProjectRequest,
)


def create_delete_project_router() -> APIRouter:
    router = APIRouter()

    @router.delete(
        "/projects/{project_id}",
        status_code=HTTPStatus.NO_CONTENT,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Delete a project",
    )
    @inject
    async def delete_project(
        project_id: UUID, command: FromDishka[DeleteProjectCommand]
    ) -> None:
        await command.execute(DeleteProjectRequest(project_id=project_id))

    return router
