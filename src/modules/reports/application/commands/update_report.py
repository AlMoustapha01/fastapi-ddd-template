"""Update report command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.reports.domain.exceptions import ReportNotFoundError
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.domain.value_objects import ReportConfigProps, ReportId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateReportRequest:
    """Request to update a report."""

    id: UUID
    title: str | None = None
    description: str | None = None
    config: ReportConfigProps | None = None


class UpdateReportResponse(TypedDict):
    """Response from updating a report."""

    id: UUID


class UpdateReportCommand:
    """Command to update an existing report."""

    def __init__(
        self,
        report_repository: ReportRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._report_repository = report_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateReportRequest) -> UpdateReportResponse:
        """
        Execute the update report command.

        :param request: The report update request
        :return: Response with the updated report ID
        :raises ReportNotFoundError: When the report is not found
        """
        log.info("Updating report: %s", request.id)

        report_id = ReportId(request.id)
        report = await self._report_repository.find_one_by_id(report_id)

        if report is None:
            log.warning("Report not found: %s", request.id)
            raise ReportNotFoundError(str(request.id))

        # Update fields if provided
        if request.title is not None:
            report.update_title(request.title)

        if request.description is not None:
            report.update_description(request.description)

        if request.config is not None:
            report.update_config(request.config)

        await self._report_repository.save(report)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("Report updated successfully: %s", report.id_.value)

        return UpdateReportResponse(id=report.id_.value)
