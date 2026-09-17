"""Get report by ID HTTP controller."""

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
from modules.reports.application.queries import (
    GetReportByIdQuery,
    GetReportByIdRequest,
    ReportDetailResponse,
)
from modules.reports.domain.exceptions import ReportNotFoundError


def create_get_report_by_id_router() -> APIRouter:
    """Create router for get report by ID endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/{report_id}",
        description=getdoc(GetReportByIdQuery),
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
        status_code=status.HTTP_200_OK,
        response_model=ReportDetailResponse,
    )
    @inject
    async def get_report_by_id(
        query: FromDishka[GetReportByIdQuery],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_report"]))],
        report_id: Annotated[UUID, Path(description="Report ID")],
    ) -> ReportDetailResponse:
        """
        Get a report by its ID.

        Args:
            query: Injected GetReportByIdQuery
            report_id: The report ID

        Returns:
            ReportDetailResponse with the report details

        Raises:
            ReportNotFoundError: When the report is not found
        """
        request_data = GetReportByIdRequest(id=report_id)
        return await query.execute(request_data)

    return router
