"""Builders of task aggregates for tests."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.tasks.domain.entities import Task, TaskProps
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle

PAST = datetime(2000, 1, 1, tzinfo=UTC)


def make_task(
    *,
    project_id: UUID | None = None,
    title: str = "Write copy",
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    """A task as loaded from storage: no pending event, timestamps in the past."""
    return Task(
        id_=TaskId.generate(),
        props=TaskProps(
            project_id=project_id or uuid4(),
            title=TaskTitle(title),
            description=TaskDescription(""),
            status=status,
        ),
        created_at_=PAST,
        updated_at_=PAST,
    )
