"""Dishka provider for reports module."""

from dishka import Provider, Scope, provide, provide_all

from core.lib.db.flusher import Flusher
from core.lib.db.main_transaction_manager_sqla import SqlaMainTransactionManager
from core.lib.db.transaction_manager import TransactionManager
from modules.reports.application.commands import (
    CreateReportCommand,
    DeleteReportCommand,
    SqlaReportFlusher,
    UpdateReportCommand,
)
from modules.reports.application.queries import (
    GetReportByIdQuery,
    GetReportsQuery,
)
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.infrastructure.mappers import ReportMapper
from modules.reports.infrastructure.repositories import ReportRepository


class ReportsProvider(Provider):
    """Provider for reports module dependencies."""

    scope = Scope.REQUEST

    # Mappers
    mappers = provide_all(
        ReportMapper,
    )

    tx_manager = provide(SqlaMainTransactionManager, provides=TransactionManager)
    report_flusher = provide(SqlaReportFlusher, provides=Flusher)

    # Repositories
    report_repository = provide(ReportRepository, provides=ReportRepositoryPort)

    # Commands
    commands = provide_all(
        CreateReportCommand,
        DeleteReportCommand,
        UpdateReportCommand,
    )

    # Queries
    queries = provide_all(
        GetReportByIdQuery,
        GetReportsQuery,
    )
