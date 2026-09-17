"""Create a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.entities import Task
from modules.tasks.domain.errors import (
    TaskProjectArchivedError,
    TaskProjectNotFoundError,
)
from modules.tasks.domain.ports import ProjectLookupPort, TaskRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTaskRequest:
    project_id: UUID
    title: str
    description: str = ""


class CreateTaskCommand:
    """
    Create a task in an active project.

    The project is locked until commit, so a concurrent archive or delete waits for
    this transaction and then sees (and cancels or deletes) the new task.
    """

    def __init__(
        self,
        repository: TaskRepositoryPort,
        project_lookup: ProjectLookupPort,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._project_lookup = project_lookup
        self._uow = uow

    async def execute(self, request: CreateTaskRequest) -> TaskDTO:
        task = Task.create(
            project_id=request.project_id,
            title=request.title,
            description=request.description,
        )
        project = await self._project_lookup.get(request.project_id, lock=True)
        if project is None:
            raise TaskProjectNotFoundError(request.project_id)
        if not project.is_active:
            raise TaskProjectArchivedError(request.project_id)
        await self._repository.add(task)
        await self._uow.commit()
        log.info("Task created: %s", task.id_.value)
        return TaskDTO.from_entity(task)
