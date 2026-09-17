"""Get reports HTTP controller."""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.db.repository.errors import EntityQueryError
from core.lib.db.repository.paginated import SortOrder
from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain.user import AuthUser
from modules.reports.application.queries import (
    GetReportsQuery,
    GetReportsRequest,
    GetReportsResponse,
)
from modules.reports.domain.exceptions import ReportValidationError
from modules.rules.domain.enums import BalanceType, ProfileType


def create_get_reports_router() -> APIRouter:
    """Create router for get reports endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/",
        description=getdoc(GetReportsQuery),
        error_map={
            ReportValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            EntityQueryError: rule(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=GetReportsResponse,
    )
    @inject
    async def get_reports(
        query: FromDishka[GetReportsQuery],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_report"]))],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
        order_by_field: Annotated[
            str | None,
            Query(description="Field to order by (e.g., 'title', 'created_at')"),
        ] = None,
        order_by_direction: Annotated[
            SortOrder, Query(description="Sort direction (ASC or DESC)")
        ] = SortOrder.ASC,
        profile_type: Annotated[
            ProfileType | None, Query(description="Filter by profile type")
        ] = None,
        balance_type: Annotated[
            BalanceType | None, Query(description="Filter by balance type")
        ] = None,
        search: Annotated[
            str | None, Query(description="Search across title and description")
        ] = None,
    ) -> GetReportsResponse:
        """
        Get all reports with pagination and filters.

        Args:
            query: Injected GetReportsQuery
            page: Page number (starts at 1)
            limit: Number of items per page (max 100)
            order_by_field: Field to order by
            order_by_direction: Sort direction
            profile_type: Filter by profile type (PREPAID, HYBRID)
            balance_type: Filter by balance type (MAIN_BALANCE, CRED)
            search: Search text across title and description

        Returns:
            GetReportsResponse with paginated reports

        Raises:
            ReportValidationError: When validation fails
        """
        request_data = GetReportsRequest(
            page=page,
            limit=limit,
            order_by_field=order_by_field,
            order_by_direction=order_by_direction,
            profile_type=profile_type,
            balance_type=balance_type,
            search=search,
        )
        return await query.execute(request_data)

    return router
