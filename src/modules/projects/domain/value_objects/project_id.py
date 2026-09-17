"""Project identifier."""

from dataclasses import dataclass

from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class ProjectId(EntityId):
    """Identity of a project."""
