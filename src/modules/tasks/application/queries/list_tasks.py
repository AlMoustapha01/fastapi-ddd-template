"""List tasks."""

from dataclasses import dataclass
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort


@dataclass(frozen=True, slots=True, kw_only=True)
class ListTasksRequest:
    page: int = 1
    size: int = 20
    project_id: UUID | None = None
    status: TaskStatus | None = None
    sort: str = "-created_at"


class ListTasksQuery:
    """Return a page of tasks, optionally filtered by project and status."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: ListTasksRequest) -> Page[TaskDTO]:
        filters: dict[str, object] = {}
        if request.project_id is not None:
            filters["project_id"] = request.project_id
        if request.status is not None:
            filters["status"] = request.status.value
        page = await self._repository.list_page(
            PageParams(page=request.page, size=request.size),
            sort=Sort.parse(request.sort),
            filters=filters,
        )
        return page.map(TaskDTO.from_entity)
