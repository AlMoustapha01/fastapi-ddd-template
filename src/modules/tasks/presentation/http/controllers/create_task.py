"""POST /tasks."""

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import CreateTaskCommand, CreateTaskRequest
from modules.tasks.presentation.http.schemas import CreateTaskBody, TaskResponse


def create_create_task_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/tasks",
        status_code=HTTPStatus.CREATED,
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Create a task in an active project",
    )
    @inject
    async def create_task(
        body: CreateTaskBody, command: FromDishka[CreateTaskCommand]
    ) -> TaskResponse:
        task = await command.execute(
            CreateTaskRequest(
                project_id=body.project_id,
                title=body.title,
                description=body.description,
            )
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
