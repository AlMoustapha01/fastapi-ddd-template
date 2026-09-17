"""Get user by ID HTTP controller."""

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
from modules.auth.domain import AuthUser
from modules.users.application.queries import (
    GetUserByIdQuery,
    GetUserByIdRequest,
    UserDetailResponse,
)
from modules.users.domain.exceptions import UserNotFoundError, UserValidationError


def create_get_user_by_id_router() -> APIRouter:
    """Create router for get user by ID endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/{user_id}",
        description=getdoc(GetUserByIdQuery),
        error_map={
            UserNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
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
        response_model=UserDetailResponse,
    )
    @inject
    async def get_user_by_id(
        query: FromDishka[GetUserByIdQuery],
        user_id: Annotated[UUID, Path(description="User ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_user"]))],
    ) -> UserDetailResponse:
        """
        Get a user by its ID.

        Args:
            query: Injected GetUserByIdQuery
            user_id: UUID of the user to retrieve

        Returns:
            UserDetailResponse with user details

        Raises:
            UserNotFoundError: When user is not found
            UserValidationError: When validation fails
        """
        request_data = GetUserByIdRequest(id=user_id)
        return await query.execute(request_data)

    return router
