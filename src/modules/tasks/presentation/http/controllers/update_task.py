"""PATCH /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import UpdateTaskCommand, UpdateTaskRequest
from modules.tasks.presentation.http.schemas import TaskResponse, UpdateTaskBody


def create_update_task_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Update an open task",
    )
    @inject
    async def update_task(
        task_id: UUID, body: UpdateTaskBody, command: FromDishka[UpdateTaskCommand]
    ) -> TaskResponse:
        task = await command.execute(
            UpdateTaskRequest(
                task_id=task_id, title=body.title, description=body.description
            )
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
