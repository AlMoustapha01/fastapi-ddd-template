"""Persistence port of the project aggregate."""

from collections.abc import Mapping
from typing import Protocol

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.domain.entities import Project
from modules.projects.domain.value_objects import ProjectId, ProjectName


class ProjectRepositoryPort(Protocol):
    async def add(self, entity: Project) -> None: ...

    async def save(self, entity: Project) -> None: ...

    async def delete(self, entity: Project) -> None: ...

    async def get_by_id(
        self, entity_id: ProjectId, *, lock: bool = False
    ) -> Project | None:
        """`lock=True`: the project cannot change until the transaction ends."""
        ...

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool: ...

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Project]: ...
