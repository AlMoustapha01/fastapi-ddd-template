"""Get reports query."""

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
from modules.reports.domain.entities.report import Report
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.domain.value_objects import ReportConfigProps
from modules.rules.domain.enums import BalanceType, ProfileType

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetReportsRequest:
    """Request to get reports with pagination."""

    page: int = 1
    limit: int = 10
    order_by_field: str | None = None
    order_by_direction: SortOrder = SortOrder.ASC
    profile_type: ProfileType | None = None
    balance_type: BalanceType | None = None
    search: str | None = None


class ReportResponse(TypedDict):
    """Report response data."""

    id: UUID
    title: str
    description: str
    profile_type: str
    balance_type: str
    config: ReportConfigProps
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class GetReportsResponse(TypedDict):
    """Paginated reports response."""

    count: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    data: list[ReportResponse]


class GetReportsQuery:
    """Query to get all reports with pagination."""

    def __init__(self, report_repository: ReportRepositoryPort) -> None:
        self._report_repository = report_repository

    async def execute(self, request: GetReportsRequest) -> GetReportsResponse:
        """
        Execute the get reports query.

        :param request: The pagination request
        :return: Paginated reports response
        """
        log.info(
            "Fetching reports: page=%d, limit=%d, profile=%s, balance=%s, search=%s",
            request.page,
            request.limit,
            request.profile_type,
            request.balance_type,
            request.search,
        )

        # Build query params
        order_by = None
        if request.order_by_field:
            order_by = OrderBy[Report](
                field=request.order_by_field,
                param=request.order_by_direction,
            )

        # Build filters
        filters: list[FilterBy[Report]] = []
        filter_groups: list[FilterGroup[Report]] = []

        if request.profile_type:
            filters.append(
                FilterBy[Report](
                    field="profile_type",
                    operator=Operator.EQ,
                    value=request.profile_type.value,
                )
            )
        if request.balance_type:
            filters.append(
                FilterBy[Report](
                    field="balance_type",
                    operator=Operator.EQ,
                    value=request.balance_type.value,
                )
            )

        # Search across title and description with OR logic
        if request.search:
            search_filters = [
                FilterBy[Report](
                    field="title",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
                FilterBy[Report](
                    field="description",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
            ]
            filter_groups.append(
                FilterGroup[Report](filters=search_filters, use_or=True)
            )

        params = PaginatedQueryParams[Report](
            page=request.page,
            limit=request.limit,
            order_by=order_by,
            filter_by=filters if filters else None,
            filter_groups=filter_groups if filter_groups else None,
        )

        # Fetch paginated reports
        paginated: Paginated[Report] = await self._report_repository.find_all_paginated(
            params
        )

        log.info(
            "Fetched %d reports (page %d/%d)",
            len(paginated.data),
            paginated.page,
            paginated.total_pages,
        )

        # Map to response
        reports_data: list[ReportResponse] = [
            ReportResponse(
                id=report.id_.value,
                title=report.props.title.value,
                description=report.props.description.value,
                profile_type=report.props.profile_type.value,
                balance_type=report.props.balance_type.value,
                config=report.props.config.to_plain_object(),
                created_by_user_id=report.props.created_by.value,
                created_at=report.created_at_,
                updated_at=report.updated_at_,
            )
            for report in paginated.data
        ]

        return GetReportsResponse(
            count=paginated.count,
            limit=paginated.limit,
            page=paginated.page,
            total_pages=paginated.total_pages,
            has_next=paginated.has_next,
            has_previous=paginated.has_previous,
            data=reports_data,
        )
