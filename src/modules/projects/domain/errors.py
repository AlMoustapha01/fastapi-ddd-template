"""Business errors of the projects module."""

from uuid import UUID

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    NotFoundError,
)


class ProjectNotFoundError(NotFoundError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' was not found.",
            code="project_not_found",
            details={"project_id": str(project_id)},
        )


class ProjectNameAlreadyExistsError(ConflictError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"A project named '{name}' already exists.",
            code="project_name_already_exists",
            details={"name": name},
        )


class ProjectAlreadyArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is already archived.",
            code="project_already_archived",
            details={"project_id": str(project_id)},
        )


class ProjectArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is archived and cannot be modified.",
            code="project_archived",
            details={"project_id": str(project_id)},
        )
