"""Update the title and/or description of a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateTaskRequest:
    task_id: UUID
    title: str | None = None
    description: str | None = None


class UpdateTaskCommand:
    """Change the title and/or description of an open task."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: UpdateTaskRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        if request.title is not None:
            task.rename(request.title)
        if request.description is not None:
            task.change_description(request.description)
        await self._repository.save(task)
        await self._uow.commit()
        log.info("Task updated: %s", request.task_id)
        return TaskDTO.from_entity(task)
