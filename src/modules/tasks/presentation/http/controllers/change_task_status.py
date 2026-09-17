"""PATCH /tasks/{task_id}/status."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
)
from modules.tasks.presentation.http.schemas import ChangeTaskStatusBody, TaskResponse


def create_change_task_status_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/tasks/{task_id}/status",
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Change the status of a task",
    )
    @inject
    async def change_task_status(
        task_id: UUID,
        body: ChangeTaskStatusBody,
        command: FromDishka[ChangeTaskStatusCommand],
    ) -> TaskResponse:
        task = await command.execute(
            ChangeTaskStatusRequest(task_id=task_id, status=body.status)
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
