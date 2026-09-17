"""Make user inactive HTTP controller."""

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
from modules.users.application.commands import (
    MakeInactiveUserCommand,
    MakeInactiveUserRequest,
    MakeInactiveUserResponse,
)
from modules.users.domain.exceptions import UserNotFoundError


def create_make_inactive_user_router() -> APIRouter:
    """Create router for make user inactive endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{user_id}/deactivate",
        description=getdoc(MakeInactiveUserCommand),
        error_map={
            UserNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=MakeInactiveUserResponse,
    )
    @inject
    async def make_user_inactive(
        command: FromDishka[MakeInactiveUserCommand],
        user_id: Annotated[UUID, Path(description="User ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_deactivate_user"]))],
    ) -> MakeInactiveUserResponse:
        """
        Deactivate a user.

        Args:
            command: Injected MakeInactiveUserCommand
            user_id: UUID of the user to deactivate

        Returns:
            MakeInactiveUserResponse with the user ID

        Raises:
            UserNotFoundError: When user is not found
        """
        request_data = MakeInactiveUserRequest(id=user_id)
        return await command.execute(request_data)

    return router
