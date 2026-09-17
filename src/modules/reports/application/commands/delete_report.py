"""Delete report command."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.reports.domain.exceptions import ReportNotFoundError
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.domain.value_objects import ReportId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteReportRequest:
    """Request to delete a report."""

    id: UUID


class DeleteReportCommand:
    """Command to delete a report."""

    def __init__(
        self,
        report_repository: ReportRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._report_repository = report_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: DeleteReportRequest) -> None:
        """
        Execute the delete report command.

        :param request: The report deletion request
        :raises ReportNotFoundError: When the report is not found
        """
        log.info("Deleting report: %s", request.id)

        report_id = ReportId(request.id)
        report = await self._report_repository.find_one_by_id(report_id)

        if report is None:
            log.warning("Report not found: %s", request.id)
            raise ReportNotFoundError(str(request.id))

        await self._report_repository.delete(report)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("Report deleted successfully: %s", request.id)
