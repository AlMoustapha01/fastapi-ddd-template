"""In-memory doubles of the tasks module."""

from collections.abc import Mapping
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.domain.entities import Task
from modules.tasks.domain.ports import (
    ProjectLookupPort,
    ProjectRef,
    TaskRepositoryPort,
)
from modules.tasks.domain.value_objects import TaskId


class InMemoryTaskRepository(TaskRepositoryPort):
    """Dictionary-backed repository; `list_page` records its arguments, never sorts."""

    def __init__(self, *tasks: Task) -> None:
        self.tasks: dict[UUID, Task] = {task.id_.value: task for task in tasks}
        self.list_calls: list[dict[str, object]] = []

    async def add(self, entity: Task) -> None:
        self.tasks[entity.id_.value] = entity

    async def save(self, entity: Task) -> None:
        self.tasks[entity.id_.value] = entity

    async def delete(self, entity: Task) -> None:
        self.tasks.pop(entity.id_.value, None)

    async def get_by_id(self, entity_id: TaskId) -> Task | None:
        return self.tasks.get(entity_id.value)

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Task]:
        self.list_calls.append({
            "params": params,
            "sort": sort,
            "filters": filters,
            "search": search,
        })
        tasks = list(self.tasks.values())
        return Page(
            items=tasks[params.offset : params.offset + params.size],
            total=len(tasks),
            page=params.page,
            size=params.size,
        )

    async def list_open_by_project(self, project_id: UUID) -> list[Task]:
        return [
            task
            for task in self.tasks.values()
            if task.props.project_id == project_id and not task.props.status.is_terminal
        ]

    async def delete_by_project(self, project_id: UUID) -> None:
        self.tasks = {
            key: task
            for key, task in self.tasks.items()
            if task.props.project_id != project_id
        }


class FakeProjectLookup(ProjectLookupPort):
    def __init__(self, *projects: ProjectRef) -> None:
        self.projects = {project.id: project for project in projects}

    async def get(self, project_id: UUID) -> ProjectRef | None:
        return self.projects.get(project_id)
