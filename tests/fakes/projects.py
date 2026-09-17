"""In-memory doubles of the projects module."""

from collections.abc import Mapping
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.domain.entities import Project
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId, ProjectName


class InMemoryProjectRepository(ProjectRepositoryPort):
    """Dictionary-backed repository; `list_page` records its arguments, never sorts."""

    def __init__(self, *projects: Project) -> None:
        self.projects: dict[UUID, Project] = {p.id_.value: p for p in projects}
        self.deleted: list[Project] = []
        self.list_calls: list[dict[str, object]] = []
        self.locked: list[UUID] = []

    async def add(self, entity: Project) -> None:
        self.projects[entity.id_.value] = entity

    async def save(self, entity: Project) -> None:
        self.projects[entity.id_.value] = entity

    async def delete(self, entity: Project) -> None:
        self.projects.pop(entity.id_.value, None)
        self.deleted.append(entity)

    async def get_by_id(
        self, entity_id: ProjectId, *, lock: bool = False
    ) -> Project | None:
        if lock:
            self.locked.append(entity_id.value)
        return self.projects.get(entity_id.value)

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool:
        return any(
            project.props.name == name and project.id_ != exclude_id
            for project in self.projects.values()
        )

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Project]:
        self.list_calls.append({
            "params": params,
            "sort": sort,
            "filters": filters,
            "search": search,
        })
        projects = list(self.projects.values())
        return Page(
            items=projects[params.offset : params.offset + params.size],
            total=len(projects),
            page=params.page,
            size=params.size,
        )
