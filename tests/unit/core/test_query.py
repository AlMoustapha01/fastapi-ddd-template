"""Whitelisted sort / filter / search helpers, compiled to SQL without a database."""

import pytest
from sqlalchemy import Select, String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.domain.errors import DomainValidationError
from core.domain.pagination import Sort, SortDirection
from core.infrastructure.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from core.infrastructure.db.query import (
    build_filters,
    build_order_by,
    build_search,
    escape_like,
)


class QueryTestBase(DeclarativeBase):
    """Separate metadata: this table never reaches the application schema."""


class ArticleModel(UUIDPrimaryKeyMixin, TimestampMixin, QueryTestBase):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))


POSTGRESQL = postgresql.dialect()  # type: ignore[no-untyped-call]


def to_sql(statement: Select[tuple[ArticleModel]]) -> str:
    return str(statement.compile(dialect=POSTGRESQL))


def test_escape_like_escapes_wildcards_and_backslashes() -> None:
    assert escape_like("50%_off\\now") == "50\\%\\_off\\\\now"


def test_order_by_applies_direction_and_primary_key_tiebreaker() -> None:
    order_by = build_order_by(
        ArticleModel, Sort("title", SortDirection.DESC), allowed={"title"}
    )

    sql = to_sql(select(ArticleModel).order_by(*order_by))

    assert "ORDER BY articles.title DESC, articles.id ASC" in sql


@pytest.mark.parametrize("field", ["status", "metadata", "__table__"])
def test_order_by_rejects_fields_outside_the_whitelist(field: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        build_order_by(ArticleModel, Sort(field), allowed={"title", "created_at"})

    assert exc_info.value.code == "invalid_sort_field"
    assert exc_info.value.details == {
        "field": field,
        "allowed": ["created_at", "title"],
    }


def test_filters_build_equality_conditions() -> None:
    conditions = build_filters(ArticleModel, {"status": "active"}, allowed={"status"})

    sql = to_sql(select(ArticleModel).where(*conditions))

    assert "WHERE articles.status = %(status_1)s" in sql


def test_filters_reject_fields_outside_the_whitelist() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        build_filters(ArticleModel, {"title": "x"}, allowed={"status"})

    assert exc_info.value.code == "invalid_filter_field"


def test_search_matches_any_field_with_an_escaped_pattern() -> None:
    conditions = build_search(ArticleModel, "50%", fields=("title", "status"))
    statement = select(ArticleModel).where(*conditions)

    sql = to_sql(statement)

    assert "articles.title ILIKE %(title_1)s ESCAPE" in sql
    assert " OR articles.status ILIKE %(status_1)s ESCAPE" in sql
    assert statement.compile().params["title_1"] == "%50\\%%"


@pytest.mark.parametrize("search", [None, ""])
def test_search_without_term_adds_no_condition(search: str | None) -> None:
    assert build_search(ArticleModel, search, fields=("title",)) == []


def test_search_without_searchable_fields_adds_no_condition() -> None:
    assert build_search(ArticleModel, "term", fields=()) == []
