"""Whitelisted sorting, filtering and searching for SQLAlchemy selects."""

from collections.abc import Iterable, Mapping
from typing import Any, cast

from sqlalchemy import ColumnElement, inspect, or_

from core.domain.errors import DomainValidationError
from core.domain.pagination import Sort, SortDirection

LIKE_ESCAPE_CHARACTER = "\\"


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so that user input is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_order_by(
    model: type[Any], sort: Sort, *, allowed: Iterable[str]
) -> list[ColumnElement[Any]]:
    _ensure_allowed(sort.field, allowed, purpose="sort")
    column = _column(model, sort.field)
    ordered = column.desc() if sort.direction is SortDirection.DESC else column.asc()
    primary_key = inspect(model).primary_key[0]
    return [ordered, primary_key.asc()]


def build_filters(
    model: type[Any], filters: Mapping[str, object], *, allowed: Iterable[str]
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    for name, value in filters.items():
        _ensure_allowed(name, allowed, purpose="filter")
        conditions.append(_column(model, name) == value)
    return conditions


def build_search(
    model: type[Any], search: str | None, *, fields: Iterable[str]
) -> list[ColumnElement[bool]]:
    names = list(fields)
    if not search or not names:
        return []
    pattern = f"%{escape_like(search)}%"
    return [
        or_(
            *(
                _column(model, name).ilike(pattern, escape=LIKE_ESCAPE_CHARACTER)
                for name in names
            )
        )
    ]


def _column(model: type[Any], name: str) -> ColumnElement[Any]:
    return cast(ColumnElement[Any], inspect(model).columns[name])


def _ensure_allowed(name: str, allowed: Iterable[str], *, purpose: str) -> None:
    allowed_names = sorted(allowed)
    if name not in allowed_names:
        raise DomainValidationError(
            f"Cannot {purpose} by '{name}'.",
            code=f"invalid_{purpose}_field",
            details={"field": name, "allowed": allowed_names},
        )
