"""Persistence port of the task aggregate."""

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.domain.entities import Task
from modules.tasks.domain.value_objects import TaskId


class TaskRepositoryPort(Protocol):
    async def add(self, entity: Task) -> None: ...

    async def save(self, entity: Task) -> None: ...

    async def delete(self, entity: Task) -> None: ...

    async def get_by_id(self, entity_id: TaskId) -> Task | None: ...

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Task]: ...

    async def list_open_by_project(self, project_id: UUID) -> list[Task]: ...

    async def delete_by_project(self, project_id: UUID) -> None: ...
