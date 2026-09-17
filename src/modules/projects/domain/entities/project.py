"""Project aggregate."""

from dataclasses import dataclass
from typing import Self

from core.domain.aggregate_root import AggregateRoot
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectAlreadyArchivedError,
    ProjectArchivedError,
)
from modules.projects.domain.events import (
    ProjectArchived,
    ProjectCreated,
    ProjectDeleted,
)
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)


@dataclass(slots=True)
class ProjectProps:
    name: ProjectName
    description: ProjectDescription
    status: ProjectStatus


class Project(AggregateRoot[ProjectId, ProjectProps]):
    """A named container of work. Archived projects are read-only."""

    @classmethod
    def create(cls, *, name: str, description: str = "") -> Self:
        project = cls(
            id_=ProjectId.generate(),
            props=ProjectProps(
                name=ProjectName(name),
                description=ProjectDescription(description),
                status=ProjectStatus.ACTIVE,
            ),
        )
        project.record_event(
            ProjectCreated(project_id=project.id_.value, name=project.props.name.value)
        )
        return project

    @property
    def is_active(self) -> bool:
        return self.props.status is ProjectStatus.ACTIVE

    def rename(self, name: str) -> None:
        self._ensure_active()
        self.props.name = ProjectName(name)
        self.touch()

    def change_description(self, description: str) -> None:
        self._ensure_active()
        self.props.description = ProjectDescription(description)
        self.touch()

    def archive(self) -> None:
        if not self.is_active:
            raise ProjectAlreadyArchivedError(self.id_.value)
        self.props.status = ProjectStatus.ARCHIVED
        self.touch()
        self.record_event(ProjectArchived(project_id=self.id_.value))

    def mark_deleted(self) -> None:
        """Announce the deletion; the repository removes the row."""
        self.record_event(ProjectDeleted(project_id=self.id_.value))

    def validate(self) -> None:
        """Invariants are enforced by the value objects."""

    def _ensure_active(self) -> None:
        if not self.is_active:
            raise ProjectArchivedError(self.id_.value)
