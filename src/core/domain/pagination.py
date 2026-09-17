"""Framework-agnostic pagination and sorting primitives."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import ceil
from typing import Final, Self

from core.domain.errors import DomainValidationError

MAX_PAGE_SIZE: Final[int] = 100


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class Sort:
    field: str
    direction: SortDirection = SortDirection.ASC

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Parse `field` (ascending) or `-field` (descending)."""
        name = raw.strip()
        direction = SortDirection.ASC
        if name.startswith("-"):
            name, direction = name[1:], SortDirection.DESC
        if not name:
            raise DomainValidationError(
                "Sort field cannot be empty.",
                code="invalid_sort_field",
                details={"sort": raw},
            )
        return cls(field=name, direction=direction)


@dataclass(frozen=True, slots=True)
class PageParams:
    page: int = 1
    size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError(
                "Page must be greater than or equal to 1.",
                code="invalid_page",
                details={"page": self.page},
            )
        if not 1 <= self.size <= MAX_PAGE_SIZE:
            raise DomainValidationError(
                f"Page size must be between 1 and {MAX_PAGE_SIZE}.",
                code="invalid_page_size",
                details={"size": self.size},
            )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: Sequence[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.size > 0 else 0

    def map[U](self, transform: Callable[[T], U]) -> "Page[U]":
        return Page(
            items=[transform(item) for item in self.items],
            total=self.total,
            page=self.page,
            size=self.size,
        )
