"""Get report by ID query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from modules.reports.domain.entities.report import Report
from modules.reports.domain.exceptions import ReportNotFoundError
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.domain.value_objects import ReportConfigProps, ReportId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetReportByIdRequest:
    """Request to get a report by ID."""

    id: UUID


class ReportDetailResponse(TypedDict):
    """Detailed report response data."""

    id: UUID
    title: str
    description: str
    profile_type: str
    balance_type: str
    config: ReportConfigProps
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class GetReportByIdQuery:
    """Query to get a report by its ID."""

    def __init__(self, report_repository: ReportRepositoryPort) -> None:
        self._report_repository = report_repository

    async def execute(self, request: GetReportByIdRequest) -> ReportDetailResponse:
        """
        Execute the get report by ID query.

        :param request: The request with report ID
        :return: Detailed report response
        :raises ReportNotFoundError: When report is not found
        """
        log.info("Fetching report by ID: %s", request.id)

        # Create ReportId value object
        report_id = ReportId(request.id)

        # Fetch report from repository
        report: Report | None = await self._report_repository.find_one_by_id(report_id)

        if report is None:
            log.warning("Report not found: %s", request.id)
            raise ReportNotFoundError(str(request.id))

        log.info("Report found: %s", report.id_.value)

        # Map to response
        return ReportDetailResponse(
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
