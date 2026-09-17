"""Business errors of the tasks module."""

from uuid import UUID

from core.domain.errors import BusinessRuleViolationError, NotFoundError
from modules.tasks.domain.enums import TaskStatus


class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: UUID) -> None:
        super().__init__(
            f"Task '{task_id}' was not found.",
            code="task_not_found",
            details={"task_id": str(task_id)},
        )


class TaskClosedError(BusinessRuleViolationError):
    def __init__(self, task_id: UUID, status: TaskStatus) -> None:
        super().__init__(
            f"Task '{task_id}' is {status} and can no longer be modified.",
            code="task_closed",
            details={"task_id": str(task_id), "status": status.value},
        )


class InvalidTaskTransitionError(BusinessRuleViolationError):
    def __init__(
        self, task_id: UUID, *, current: TaskStatus, target: TaskStatus
    ) -> None:
        super().__init__(
            f"Task '{task_id}' cannot move from {current} to {target}.",
            code="invalid_task_transition",
            details={
                "task_id": str(task_id),
                "current": current.value,
                "target": target.value,
            },
        )


class TaskProjectNotFoundError(NotFoundError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' was not found.",
            code="task_project_not_found",
            details={"project_id": str(project_id)},
        )


class TaskProjectArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is archived: no task can be added to it.",
            code="task_project_archived",
            details={"project_id": str(project_id)},
        )
