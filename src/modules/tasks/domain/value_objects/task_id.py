"""Task identifier."""

from dataclasses import dataclass

from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class TaskId(EntityId):
    """Identity of a task."""
