"""Task aggregate."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Self
from uuid import UUID

from core.domain.aggregate_root import AggregateRoot
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import InvalidTaskTransitionError, TaskClosedError
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle

ALLOWED_TRANSITIONS: Final[Mapping[TaskStatus, frozenset[TaskStatus]]] = (
    MappingProxyType({
        TaskStatus.TODO: frozenset({
            TaskStatus.IN_PROGRESS,
            TaskStatus.DONE,
            TaskStatus.CANCELLED,
        }),
        TaskStatus.IN_PROGRESS: frozenset({TaskStatus.DONE, TaskStatus.CANCELLED}),
        TaskStatus.DONE: frozenset(),
        TaskStatus.CANCELLED: frozenset(),
    })
)


@dataclass(slots=True)
class TaskProps:
    project_id: UUID
    title: TaskTitle
    description: TaskDescription
    status: TaskStatus


class Task(AggregateRoot[TaskId, TaskProps]):
    """
    A unit of work that belongs to a project.

    Lifecycle: todo → in_progress → done, and any open task can be cancelled.
    Done and cancelled tasks are closed: they can no longer change.
    """

    @classmethod
    def create(cls, *, project_id: UUID, title: str, description: str = "") -> Self:
        return cls(
            id_=TaskId.generate(),
            props=TaskProps(
                project_id=project_id,
                title=TaskTitle(title),
                description=TaskDescription(description),
                status=TaskStatus.TODO,
            ),
        )

    def rename(self, title: str) -> None:
        self._ensure_open()
        self.props.title = TaskTitle(title)
        self.touch()

    def change_description(self, description: str) -> None:
        self._ensure_open()
        self.props.description = TaskDescription(description)
        self.touch()

    def start(self) -> None:
        self.change_status(TaskStatus.IN_PROGRESS)

    def complete(self) -> None:
        self.change_status(TaskStatus.DONE)

    def cancel(self) -> None:
        self.change_status(TaskStatus.CANCELLED)

    def change_status(self, target: TaskStatus) -> None:
        current = self.props.status
        if target not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTaskTransitionError(
                self.id_.value, current=current, target=target
            )
        self.props.status = target
        self.touch()

    def validate(self) -> None:
        """Invariants are enforced by the value objects."""

    def _ensure_open(self) -> None:
        if self.props.status.is_terminal:
            raise TaskClosedError(self.id_.value, self.props.status)
