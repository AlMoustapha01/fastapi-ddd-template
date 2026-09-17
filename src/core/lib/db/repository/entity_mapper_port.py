from typing import Any, Protocol, TypeVar

from core.lib.base.entity import Entity
from core.lib.db.model_base import Base

T = TypeVar("T", bound=Entity[Any, Any])
M = TypeVar("M", bound=Base)


class EntityMapperPort[T, M](Protocol):
    """Contract for mapping between domain entities and persistence models."""

    def to_model(self, entity: T) -> M:
        """Convert a domain entity into its ORM model representation."""
        ...

    def to_entity(self, model: M) -> T:
        """Convert an ORM model into its domain entity representation."""
        ...
