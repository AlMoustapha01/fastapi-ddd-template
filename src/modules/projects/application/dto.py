"""Data returned by the use cases of the projects module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectDTO:
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, project: Project) -> Self:
        return cls(
            id=project.id_.value,
            name=project.props.name.value,
            description=project.props.description.value,
            status=project.props.status,
            created_at=project.created_at_,
            updated_at=project.updated_at_,
        )
