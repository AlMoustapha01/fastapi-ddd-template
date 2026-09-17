"""Get one task."""

from dataclasses import dataclass
from uuid import UUID

from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId


@dataclass(frozen=True, slots=True, kw_only=True)
class GetTaskByIdRequest:
    task_id: UUID


class GetTaskByIdQuery:
    """Return one task."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: GetTaskByIdRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        return TaskDTO.from_entity(task)
