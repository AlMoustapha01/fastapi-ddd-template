"""Delete a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTaskRequest:
    task_id: UUID


class DeleteTaskCommand:
    """Delete a task."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: DeleteTaskRequest) -> None:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        await self._repository.delete(task)
        await self._uow.commit()
        log.info("Task deleted: %s", request.task_id)
