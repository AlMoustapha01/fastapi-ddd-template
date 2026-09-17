"""Delete User HTTP controller."""

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
    DeleteUserCommand,
    DeleteUserRequest,
)
from modules.users.domain.exceptions import UserNotFoundError


def create_delete_user_router() -> APIRouter:
    """Create router for delete User endpoint."""
    router = ErrorAwareRouter()

    @router.delete(
        "/{user_id}",
        description=getdoc(DeleteUserCommand),
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
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_user(
        command: FromDishka[DeleteUserCommand],
        user_id: Annotated[UUID, Path(description="User ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_delete_user"]))],
    ) -> None:
        """
        Delete a user by ID.

        Args:
            command: Injected DeleteUserCommand
            user_id: UUID of the user to delete

        Raises:
            UserNotFoundError: When user is not found
        """
        request_data = DeleteUserRequest(id=user_id)
        await command.execute(request_data)

    return router
