"""Get users HTTP controller."""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.db.repository.paginated import SortOrder
from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.users.application.queries import (
    GetUsersQuery,
    GetUsersRequest,
    GetUsersResponse,
)
from modules.users.domain.exceptions import UserValidationError


def create_get_users_router() -> APIRouter:
    """Create router for get users endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/",
        description=getdoc(GetUsersQuery),
        error_map={
            UserValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=GetUsersResponse,
    )
    @inject
    async def get_users(
        query: FromDishka[GetUsersQuery],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_user"]))],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
        order_by_field: Annotated[
            str | None,
            Query(description="Field to order by (e.g., 'name', 'created_at')"),
        ] = None,
        order_by_direction: Annotated[
            SortOrder, Query(description="Sort direction (ASC or DESC)")
        ] = SortOrder.ASC,
        group_id: Annotated[
            str | None,
            Query(description="Filter by Keycloak group ID"),
        ] = None,
        is_active: Annotated[
            bool | None,
            Query(description="Filter by active status"),
        ] = None,
        search: Annotated[
            str | None,
            Query(description="Search by name, email, or username (case-insensitive)"),
        ] = None,
    ) -> GetUsersResponse:
        """
        Get all users with pagination.

        Args:
            query: Injected GetUsersQuery
            page: Page number (starts at 1)
            limit: Number of items per page (max 100)
            order_by_field: Field to order by
            order_by_direction: Sort direction
            group_id: Filter by Keycloak group ID
            is_active: Filter by active status
            search: Search by name, email, or username (case-insensitive)

        Returns:
            GetUsersResponse with paginated users

        Raises:
            UserValidationError: When validation fails
        """
        request_data = GetUsersRequest(
            page=page,
            limit=limit,
            order_by_field=order_by_field,
            order_by_direction=order_by_direction,
            group_id=group_id,
            is_active=is_active,
            search=search,
        )
        return await query.execute(request_data)

    return router
