"""Data returned by the use cases of the tasks module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class TaskDTO:
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, task: Task) -> Self:
        return cls(
            id=task.id_.value,
            project_id=task.props.project_id,
            title=task.props.title.value,
            description=task.props.description.value,
            status=task.props.status,
            created_at=task.created_at_,
            updated_at=task.updated_at_,
        )
