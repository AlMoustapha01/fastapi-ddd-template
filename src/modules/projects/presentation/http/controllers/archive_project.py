"""POST /projects/{project_id}/archive."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
)
from modules.projects.presentation.http.schemas import ProjectResponse


def create_archive_project_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/projects/{project_id}/archive",
        response_model=ProjectResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT),
        summary="Archive a project",
    )
    @inject
    async def archive_project(
        project_id: UUID, command: FromDishka[ArchiveProjectCommand]
    ) -> ProjectResponse:
        project = await command.execute(ArchiveProjectRequest(project_id=project_id))
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
