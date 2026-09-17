"""Pagination types and utilities for repository queries."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import TypeVar
from uuid import UUID

T = TypeVar("T")


class Operator(StrEnum):
    """Query filter operators."""

    EQ = "eq"  # Equal
    IN = "in"  # In list
    BTW = "btw"  # Between
    ILIKE = "ilike"  # Case-insensitive like


class SortOrder(StrEnum):
    """Sort order for query results."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True, slots=True)
class OrderBy[T]:
    """Order by clause for queries."""

    field: str
    param: SortOrder


@dataclass(frozen=True, slots=True)
class FilterBy[T]:
    """Filter clause for queries."""

    field: str
    operator: Operator
    value: (
        str
        | list[str]
        | int
        | list[int]
        | float
        | list[float]
        | bool
        | list[bool]
        | datetime
        | list[datetime]
        | UUID
        | None
    )


@dataclass(frozen=True, slots=True)
class FilterGroup[T]:
    """Group of filters combined with OR logic."""

    filters: Sequence[FilterBy[T] | FilterGroup[T]]
    use_or: bool = True


@dataclass(frozen=True, slots=True)
class PaginatedQueryParams[T]:
    """Query parameters for paginated queries."""

    limit: int = 10
    page: int = 1
    filter_by: Sequence[FilterBy[T] | FilterGroup[T]] | None = None
    filter_groups: Sequence[FilterGroup[T]] | None = None
    order_by: OrderBy[T] | None = None


@dataclass(frozen=True, slots=True)
class Paginated[T]:
    """Paginated result container."""

    count: int
    limit: int
    page: int
    data: tuple[T, ...]

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.limit <= 0:
            return 0
        return (self.count + self.limit - 1) // self.limit

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
