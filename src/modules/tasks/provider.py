"""Dishka provider of the tasks module."""

from dishka import Provider, Scope, provide, provide_all

from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    UpdateTaskCommand,
)
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)
from modules.tasks.application.queries import GetTaskByIdQuery, ListTasksQuery
from modules.tasks.domain.ports import ProjectLookupPort, TaskRepositoryPort
from modules.tasks.infrastructure.adapters import ProjectsModuleLookup
from modules.tasks.infrastructure.repositories import SqlaTaskRepository


class TasksProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(SqlaTaskRepository, provides=TaskRepositoryPort)
    project_lookup = provide(ProjectsModuleLookup, provides=ProjectLookupPort)
    use_cases = provide_all(
        CreateTaskCommand,
        UpdateTaskCommand,
        ChangeTaskStatusCommand,
        DeleteTaskCommand,
        GetTaskByIdQuery,
        ListTasksQuery,
    )
    event_handlers = provide_all(
        CancelTasksOnProjectArchived, DeleteTasksOnProjectDeleted
    )
