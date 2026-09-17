"""POST /projects."""

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    CreateProjectCommand,
    CreateProjectRequest,
)
from modules.projects.presentation.http.schemas import (
    CreateProjectBody,
    ProjectResponse,
)


def create_create_project_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/projects",
        status_code=HTTPStatus.CREATED,
        response_model=ProjectResponse,
        responses=error_responses(
            HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Create a project",
    )
    @inject
    async def create_project(
        body: CreateProjectBody, command: FromDishka[CreateProjectCommand]
    ) -> ProjectResponse:
        project = await command.execute(
            CreateProjectRequest(name=body.name, description=body.description)
        )
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
