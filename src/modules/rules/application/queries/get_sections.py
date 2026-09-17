"""Get sections query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from core.lib.db.repository.paginated import (
    FilterBy,
    FilterGroup,
    Operator,
    OrderBy,
    Paginated,
    PaginatedQueryParams,
    SortOrder,
)
from modules.rules.domain.entities.section import Section
from modules.rules.domain.enums import SectionStatus
from modules.rules.domain.ports import SectionRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetSectionsRequest:
    """Request to get sections with pagination."""

    page: int = 1
    limit: int = 10
    order_by_field: str | None = None
    order_by_direction: SortOrder = SortOrder.ASC
    status: SectionStatus | None = None
    search: str | None = None
    start_created_at: datetime | None = None
    end_created_at: datetime | None = None


class SectionResponse(TypedDict):
    """Section response data."""

    id: UUID
    name: str
    slug: str
    description: str
    status: str
    created_at: datetime
    created_by_user_id: UUID


class GetSectionsResponse(TypedDict):
    """Paginated sections response."""

    count: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    data: list[SectionResponse]


class GetSectionsQuery:
    """Query to get all sections with pagination."""

    def __init__(self, section_repository: SectionRepositoryPort) -> None:
        self._section_repository = section_repository

    async def execute(self, request: GetSectionsRequest) -> GetSectionsResponse:
        """
        Execute the get sections query.

        :param request: The pagination request
        :return: Paginated sections response
        """
        log.info(
            "Fetching sections: page=%d, limit=%d, status=%s, search=%s",
            request.page,
            request.limit,
            request.status,
            request.search,
        )

        # Build query params
        order_by = None
        if request.order_by_field:
            order_by = OrderBy[Section](
                field=request.order_by_field,
                param=request.order_by_direction,
            )

        # Build filters
        filters: list[FilterBy[Section]] = []
        filter_groups: list[FilterGroup[Section]] = []

        if request.status:
            filters.append(
                FilterBy[Section](
                    field="status",
                    operator=Operator.EQ,
                    value=request.status.value,
                )
            )

        if request.start_created_at and request.end_created_at:
            filters.append(
                FilterBy[Section](
                    field="created_at",
                    operator=Operator.BTW,
                    value=[request.start_created_at, request.end_created_at],
                )
            )

        # Search across name and slug with OR logic
        if request.search:
            search_filters = [
                FilterBy[Section](
                    field="name",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
                FilterBy[Section](
                    field="description",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
            ]
            filter_groups.append(
                FilterGroup[Section](filters=search_filters, use_or=True)
            )

        params = PaginatedQueryParams[Section](
            page=request.page,
            limit=request.limit,
            order_by=order_by,
            filter_by=filters if filters else None,
            filter_groups=filter_groups if filter_groups else None,
        )

        # Fetch paginated sections
        paginated: Paginated[
            Section
        ] = await self._section_repository.find_all_paginated(params)

        log.info(
            "Fetched %d sections (page %d/%d)",
            len(paginated.data),
            paginated.page,
            paginated.total_pages,
        )

        # Map to response
        sections_data: list[SectionResponse] = [
            SectionResponse(
                id=section.id_.value,
                name=section.props.name,
                slug=section.props.slug.value,
                description=section.props.description,
                status=section.props.status.value,
                created_at=section.created_at_,
                created_by_user_id=section.props.created_by_user_id,
            )
            for section in paginated.data
        ]

        return GetSectionsResponse(
            count=paginated.count,
            limit=paginated.limit,
            page=paginated.page,
            total_pages=paginated.total_pages,
            has_next=paginated.has_next,
            has_previous=paginated.has_previous,
            data=sections_data,
        )
