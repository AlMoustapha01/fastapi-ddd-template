"""Create report command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.reports.domain.entities.report import CreateReportProps, Report
from modules.reports.domain.exceptions import ReportAlreadyExistsError
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.domain.value_objects import ReportConfigProps
from modules.rules.domain.enums import BalanceType, ProfileType

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateReportRequest:
    """Request to create a new report."""

    title: str
    description: str
    profile_type: ProfileType
    balance_type: BalanceType
    config: ReportConfigProps
    created_by: UUID


class CreateReportResponse(TypedDict):
    """Response from creating a report."""

    id: UUID


class CreateReportCommand:
    """Command to create a new report."""

    def __init__(
        self,
        report_repository: ReportRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._report_repository = report_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateReportRequest) -> CreateReportResponse:
        """
        Execute the create report command.

        :param request: The report creation request
        :return: Response with the created report ID
        :raises ReportAlreadyExistsError: When a report with the same title exists
        """
        log.info("Creating report: %s", request.title)

        report = Report.create(
            props=CreateReportProps(
                title=request.title,
                description=request.description,
                profile_type=request.profile_type,
                balance_type=request.balance_type,
                config=request.config,
                created_by=request.created_by,
            )
        )

        await self._report_repository.add(report)

        try:
            await self._flusher.flush()
        except ReportAlreadyExistsError:
            log.warning("Report already exists with title: %s", request.title)
            raise

        await self._transaction_manager.commit()

        log.info("Report created successfully: %s", report.id_.value)

        return CreateReportResponse(id=report.id_.value)
