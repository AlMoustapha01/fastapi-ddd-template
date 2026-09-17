"""Mapping contract between domain entities and ORM models."""

from typing import Protocol


class EntityMapper[TEntity, TModel](Protocol):
    def to_model(self, entity: TEntity) -> TModel: ...

    def to_entity(self, model: TModel) -> TEntity: ...
