"""GET /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.queries import GetTaskByIdQuery, GetTaskByIdRequest
from modules.tasks.presentation.http.schemas import TaskResponse


def create_get_task_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Get a task",
    )
    @inject
    async def get_task(
        task_id: UUID, query: FromDishka[GetTaskByIdQuery]
    ) -> TaskResponse:
        task = await query.execute(GetTaskByIdRequest(task_id=task_id))
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
