"""Pagination and sorting primitives."""

import pytest

from core.domain.errors import DomainValidationError
from core.domain.pagination import (
    MAX_PAGE_SIZE,
    Page,
    PageParams,
    Sort,
    SortDirection,
)


class TestSort:
    def test_parses_ascending_field(self) -> None:
        assert Sort.parse("name") == Sort("name", SortDirection.ASC)

    def test_parses_descending_field(self) -> None:
        assert Sort.parse("-created_at") == Sort("created_at", SortDirection.DESC)

    @pytest.mark.parametrize("raw", ["", "-", "   "])
    def test_rejects_empty_field(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            Sort.parse(raw)

        assert exc_info.value.code == "invalid_sort_field"


class TestPageParams:
    def test_offset(self) -> None:
        assert PageParams(page=3, size=20).offset == 40

    @pytest.mark.parametrize(
        ("page", "size", "code"),
        [
            (0, 20, "invalid_page"),
            (1, 0, "invalid_page_size"),
            (1, MAX_PAGE_SIZE + 1, "invalid_page_size"),
        ],
    )
    def test_rejects_out_of_range_values(self, page: int, size: int, code: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            PageParams(page=page, size=size)

        assert exc_info.value.code == code


class TestPage:
    @pytest.mark.parametrize(
        ("total", "size", "pages"), [(0, 20, 0), (20, 20, 1), (21, 20, 2), (5, 0, 0)]
    )
    def test_pages(self, total: int, size: int, pages: int) -> None:
        assert Page[int](items=[], total=total, page=1, size=size).pages == pages

    def test_map_transforms_items_and_keeps_metadata(self) -> None:
        page = Page[int](items=[1, 2], total=5, page=2, size=2)

        assert page.map(str) == Page[str](items=["1", "2"], total=5, page=2, size=2)
