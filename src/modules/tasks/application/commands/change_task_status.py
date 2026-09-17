"""Move a task through its lifecycle."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeTaskStatusRequest:
    task_id: UUID
    status: TaskStatus


class ChangeTaskStatusCommand:
    """Change the status of a task (todo → in_progress → done, or cancelled)."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: ChangeTaskStatusRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        task.change_status(request.status)
        await self._repository.save(task)
        await self._uow.commit()
        log.info("Task %s moved to %s", request.task_id, request.status)
        return TaskDTO.from_entity(task)
