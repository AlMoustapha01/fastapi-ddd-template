"""GET /tasks."""

from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query

from core.domain.pagination import MAX_PAGE_SIZE
from core.presentation.http.errors import error_responses
from core.presentation.http.pagination import PageResponse, to_page_response
from modules.tasks.application.queries import ListTasksQuery, ListTasksRequest
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.presentation.http.schemas import SORT_DESCRIPTION, TaskResponse


def create_list_tasks_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/tasks",
        response_model=PageResponse[TaskResponse],
        responses=error_responses(HTTPStatus.UNPROCESSABLE_CONTENT),
        summary="List tasks",
    )
    @inject
    async def list_tasks(
        query: FromDishka[ListTasksQuery],
        page: Annotated[int, Query(ge=1)] = 1,
        size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
        project_id: Annotated[UUID | None, Query()] = None,
        status: Annotated[TaskStatus | None, Query()] = None,
        sort: Annotated[str, Query(description=SORT_DESCRIPTION)] = "-created_at",
    ) -> PageResponse[TaskResponse]:
        result = await query.execute(
            ListTasksRequest(
                page=page, size=size, project_id=project_id, status=status, sort=sort
            )
        )
        return to_page_response(result, TaskResponse)

    return router
