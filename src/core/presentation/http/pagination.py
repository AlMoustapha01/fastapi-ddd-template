"""Paginated HTTP responses."""

from pydantic import BaseModel

from core.domain.pagination import Page


class PageResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def to_page_response[T, R: BaseModel](
    page: Page[T], item_type: type[R]
) -> PageResponse[R]:
    """Validate every item (usually a DTO) of a domain page into `item_type`."""
    return PageResponse(
        items=[
            item_type.model_validate(item, from_attributes=True) for item in page.items
        ],
        total=page.total,
        page=page.page,
        size=page.size,
        pages=page.pages,
    )
