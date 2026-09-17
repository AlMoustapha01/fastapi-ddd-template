"""Cross-module reactions to project events, inside one transaction."""

from typing import override
from uuid import UUID

import pytest
from dishka import AsyncContainer, Provider, Scope, provide

from app.main import create_app
from core.application.event_bus import EventHandler, EventHandlerRegistry
from core.infrastructure.settings import Settings
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
    CreateProjectCommand,
    CreateProjectRequest,
    DeleteProjectCommand,
    DeleteProjectRequest,
)
from modules.projects.application.dto import ProjectDTO
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.public import ProjectArchived
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
    CreateTaskCommand,
    CreateTaskRequest,
)
from modules.tasks.application.dto import TaskDTO
from modules.tasks.application.event_handlers import CancelTasksOnProjectArchived
from modules.tasks.application.queries import GetTaskByIdQuery, GetTaskByIdRequest
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import TaskNotFoundError


async def create_project(container: AsyncContainer, name: str) -> ProjectDTO:
    async with container() as scope:
        command = await scope.get(CreateProjectCommand)
        return await command.execute(CreateProjectRequest(name=name))


async def create_task(
    container: AsyncContainer, project_id: UUID, title: str
) -> TaskDTO:
    async with container() as scope:
        command = await scope.get(CreateTaskCommand)
        return await command.execute(
            CreateTaskRequest(project_id=project_id, title=title)
        )


async def get_task(container: AsyncContainer, task_id: UUID) -> TaskDTO:
    async with container() as scope:
        query = await scope.get(GetTaskByIdQuery)
        return await query.execute(GetTaskByIdRequest(task_id=task_id))


async def test_archiving_a_project_cancels_its_open_tasks(
    container: AsyncContainer,
) -> None:
    project = await create_project(container, "Website")
    todo = await create_task(container, project.id, "Todo")
    done = await create_task(container, project.id, "Done")
    async with container() as scope:
        await (await scope.get(ChangeTaskStatusCommand)).execute(
            ChangeTaskStatusRequest(task_id=done.id, status=TaskStatus.DONE)
        )

    async with container() as scope:
        await (await scope.get(ArchiveProjectCommand)).execute(
            ArchiveProjectRequest(project_id=project.id)
        )

    assert (await get_task(container, todo.id)).status is TaskStatus.CANCELLED
    assert (await get_task(container, done.id)).status is TaskStatus.DONE


async def test_deleting_a_project_deletes_its_tasks(container: AsyncContainer) -> None:
    project = await create_project(container, "Website")
    other_project = await create_project(container, "Intranet")
    task = await create_task(container, project.id, "Todo")
    other_task = await create_task(container, other_project.id, "Todo")

    async with container() as scope:
        await (await scope.get(DeleteProjectCommand)).execute(
            DeleteProjectRequest(project_id=project.id)
        )

    with pytest.raises(TaskNotFoundError):
        await get_task(container, task.id)
    assert (await get_task(container, other_task.id)).id == other_task.id


class ExplodingHandler(EventHandler[ProjectArchived]):
    @override
    async def handle(self, event: ProjectArchived) -> None:
        raise RuntimeError("boom")


class ExplodingHandlersProvider(Provider):
    scope = Scope.REQUEST

    handler = provide(ExplodingHandler)

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={ProjectArchived: (CancelTasksOnProjectArchived, ExplodingHandler)}
        )


async def test_a_failing_handler_rolls_back_the_whole_transaction(
    settings: Settings,
) -> None:
    app = create_app(settings, ExplodingHandlersProvider())
    container: AsyncContainer = app.state.dishka_container
    try:
        project = await create_project(container, "Website")
        task = await create_task(container, project.id, "Todo")

        async with container() as scope:
            command = await scope.get(ArchiveProjectCommand)
            with pytest.raises(RuntimeError, match="boom"):
                await command.execute(ArchiveProjectRequest(project_id=project.id))

        async with container() as scope:
            query = await scope.get(GetProjectByIdQuery)
            reloaded = await query.execute(GetProjectByIdRequest(project_id=project.id))
        assert reloaded.status is ProjectStatus.ACTIVE
        assert (await get_task(container, task.id)).status is TaskStatus.TODO
    finally:
        await container.close()
