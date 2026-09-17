"""Repository interfaces and utilities."""

from .base_repository import BaseRepository
from .base_repository_port import BaseRepositoryPort
from .entity_mapper_port import EntityMapperPort
from .errors import (
    EntityAddError,
    EntityDeleteError,
    EntityNotFoundError,
    EntityQueryError,
    EntitySaveError,
    RepositoryError,
)
from .paginated import (
    FilterBy,
    Operator,
    OrderBy,
    Paginated,
    PaginatedQueryParams,
    SortOrder,
)

__all__ = [
    "BaseRepository",
    "BaseRepositoryPort",
    "EntityAddError",
    "EntityDeleteError",
    "EntityMapperPort",
    "EntityNotFoundError",
    "EntityQueryError",
    "EntitySaveError",
    "FilterBy",
    "Operator",
    "OrderBy",
    "Paginated",
    "PaginatedQueryParams",
    "RepositoryError",
    "SortOrder",
]
