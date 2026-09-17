"""List projects."""

from dataclasses import dataclass

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.ports import ProjectRepositoryPort


@dataclass(frozen=True, slots=True, kw_only=True)
class ListProjectsRequest:
    page: int = 1
    size: int = 20
    status: ProjectStatus | None = None
    search: str | None = None
    sort: str = "-created_at"


class ListProjectsQuery:
    """Return a page of projects, optionally filtered by status and name."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: ListProjectsRequest) -> Page[ProjectDTO]:
        filters: dict[str, object] = {}
        if request.status is not None:
            filters["status"] = request.status.value
        page = await self._repository.list_page(
            PageParams(page=request.page, size=request.size),
            sort=Sort.parse(request.sort),
            filters=filters,
            search=request.search,
        )
        return page.map(ProjectDTO.from_entity)
