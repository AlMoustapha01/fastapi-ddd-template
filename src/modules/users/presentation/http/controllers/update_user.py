"""Update user HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.users.application.commands import (
    UpdateUserCommand,
    UpdateUserRequest,
    UpdateUserResponse,
)
from modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UserValidationError,
)


class UpdateUserRequestPydantic(BaseModel):
    """Pydantic model for updating user details."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(
        None, min_length=1, max_length=255, description="User full name"
    )
    email: str | None = Field(
        None, min_length=1, max_length=255, description="User email address"
    )
    username: str | None = Field(
        None, min_length=3, max_length=100, description="Username"
    )


def create_update_user_router() -> APIRouter:
    """Create router for update user details endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{user_id}",
        description=getdoc(UpdateUserCommand),
        error_map={
            UserNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            UserValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            UserAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=UpdateUserResponse,
    )
    @inject
    async def update_user_details(
        command: FromDishka[UpdateUserCommand],
        user_id: Annotated[UUID, Path(description="User ID")],
        request_data_pydantic: UpdateUserRequestPydantic,
        _: Annotated[AuthUser, Depends(require_roles(["perm_edit_user"]))],
    ) -> UpdateUserResponse:
        """
        Update user details (name, email, username).
        """
        request_data = UpdateUserRequest(
            id=user_id,
            name=request_data_pydantic.name,
            email=request_data_pydantic.email,
            username=request_data_pydantic.username,
        )
        return await command.execute(request_data)

    return router
