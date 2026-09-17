"""GET /projects."""

from http import HTTPStatus
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query

from core.domain.pagination import MAX_PAGE_SIZE
from core.presentation.http.errors import error_responses
from core.presentation.http.pagination import PageResponse, to_page_response
from modules.projects.application.queries import (
    ListProjectsQuery,
    ListProjectsRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.presentation.http.schemas import (
    SORT_DESCRIPTION,
    ProjectResponse,
)


def create_list_projects_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/projects",
        response_model=PageResponse[ProjectResponse],
        responses=error_responses(HTTPStatus.UNPROCESSABLE_CONTENT),
        summary="List projects",
    )
    @inject
    async def list_projects(
        query: FromDishka[ListProjectsQuery],
        page: Annotated[int, Query(ge=1)] = 1,
        size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
        status: Annotated[ProjectStatus | None, Query()] = None,
        search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
        sort: Annotated[str, Query(description=SORT_DESCRIPTION)] = "-created_at",
    ) -> PageResponse[ProjectResponse]:
        result = await query.execute(
            ListProjectsRequest(
                page=page, size=size, status=status, search=search, sort=sort
            )
        )
        return to_page_response(result, ProjectResponse)

    return router
