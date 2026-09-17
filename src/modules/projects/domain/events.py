"""Domain events of the projects module (public: see `modules.projects.public`)."""

from dataclasses import dataclass
from uuid import UUID

from core.domain.events import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectCreated(DomainEvent):
    project_id: UUID
    name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectArchived(DomainEvent):
    project_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectDeleted(DomainEvent):
    project_id: UUID
