"""Delete report HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain.user import AuthUser
from modules.reports.application.commands import (
    DeleteReportCommand,
    DeleteReportRequest,
)
from modules.reports.domain.exceptions import ReportNotFoundError


def create_delete_report_router() -> APIRouter:
    """Create router for report deletion endpoint."""
    router = ErrorAwareRouter()

    @router.delete(
        "/{report_id}",
        description=getdoc(DeleteReportCommand),
        error_map={
            ReportNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_report(
        command: FromDishka[DeleteReportCommand],
        _: Annotated[AuthUser, Depends(require_roles(["perm_delete_report"]))],
        report_id: Annotated[UUID, Path(description="Report ID")],
    ) -> None:
        """
        Delete a report.

        Args:
            command: Injected DeleteReportCommand
            report_id: The report ID

        Raises:
            ReportNotFoundError: When the report is not found
        """
        request_data = DeleteReportRequest(id=report_id)
        await command.execute(request_data)

    return router
