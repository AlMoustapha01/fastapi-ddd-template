"""Base repository port interface."""

from typing import Any, Protocol, TypeVar

from core.lib.base.entity import Entity
from core.lib.db.repository.paginated import Paginated, PaginatedQueryParams

T = TypeVar("T", bound=Entity[Any, Any])


class BaseRepositoryPort[T](Protocol):
    """Base repository port for entity persistence operations."""

    async def add(self, entity: T | list[T]) -> None:
        """Add an entity or a list of entities to the repository."""

    async def save(self, entity: T | list[T]) -> None:
        """Save an entity or a list of entities to the repository."""

    async def delete(self, entity: T | list[T]) -> None:
        """Delete an entity or a list of entities from the repository."""

    async def find_one_by_id(self, id_: Any) -> T | None:
        """Find an entity by its id."""

    async def find_all_paginated(self, params: PaginatedQueryParams[T]) -> Paginated[T]:
        """Find all entities paginated with optional filtering and sorting."""
