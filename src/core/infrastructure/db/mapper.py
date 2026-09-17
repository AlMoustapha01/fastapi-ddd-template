"""Mapping contract between domain entities and ORM models."""

from typing import Protocol


class EntityMapper[TEntity, TModel](Protocol):
    def to_model(self, entity: TEntity) -> TModel:
        """Build a new model (for insertion) from an entity."""
        ...

    def apply(self, entity: TEntity, model: TModel) -> None:
        """Copy the mutable state of an entity onto an already loaded model."""
        ...

    def to_entity(self, model: TModel) -> TEntity: ...
