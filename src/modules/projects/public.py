"""
Public API of the projects module.

Other modules may import this file only. It exposes read-only summaries and the
domain events other modules may react to, never entities or repositories.
"""

from dataclasses import dataclass
from uuid import UUID

from modules.projects.domain.events import ProjectArchived, ProjectDeleted
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

__all__ = ["ProjectArchived", "ProjectDeleted", "ProjectSummary", "ProjectsPublicApi"]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectSummary:
    id: UUID
    name: str
    is_active: bool


class ProjectsPublicApi:
    """Read-only facade used by other modules."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def get_summary(
        self, project_id: UUID, *, lock: bool = False
    ) -> ProjectSummary | None:
        """
        Return a summary of the project, or `None` if it does not exist.

        `lock=True` keeps the project from being archived or deleted until the
        caller's transaction ends (use it before writing data that depends on it).
        """
        project = await self._repository.get_by_id(ProjectId(project_id), lock=lock)
        if project is None:
            return None
        return ProjectSummary(
            id=project.id_.value,
            name=project.props.name.value,
            is_active=project.is_active,
        )
