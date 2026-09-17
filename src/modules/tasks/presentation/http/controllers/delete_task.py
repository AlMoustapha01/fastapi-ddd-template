"""DELETE /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import DeleteTaskCommand, DeleteTaskRequest


def create_delete_task_router() -> APIRouter:
    router = APIRouter()

    @router.delete(
        "/tasks/{task_id}",
        status_code=HTTPStatus.NO_CONTENT,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Delete a task",
    )
    @inject
    async def delete_task(
        task_id: UUID, command: FromDishka[DeleteTaskCommand]
    ) -> None:
        await command.execute(DeleteTaskRequest(task_id=task_id))

    return router
