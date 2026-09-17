"""Create user HTTP controller."""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.users.application.commands import (
    CreateUserCommand,
    CreateUserRequest,
    CreateUserResponse,
)
from modules.users.domain.exceptions import (
    UserAlreadyExistsError,
    UserValidationError,
)


class CreateUserRequestPydantic(BaseModel):
    """
    Pydantic model for create user request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    email: str = Field(
        ..., min_length=1, max_length=255, description="User email address"
    )
    username: str = Field(
        ..., min_length=3, max_length=100, description="Unique username"
    )
    keycloak_id: str = Field(..., min_length=1, description="Keycloak user identifier")


def create_create_user_router() -> APIRouter:
    """Create router for user creation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/",
        description=getdoc(CreateUserCommand),
        error_map={
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
        status_code=status.HTTP_201_CREATED,
        response_model=CreateUserResponse,
    )
    @inject
    async def create_user(
        request_data_pydantic: CreateUserRequestPydantic,
        command: FromDishka[CreateUserCommand],
        _: Annotated[AuthUser, Depends(require_roles(["perm_create_user"]))],
    ) -> CreateUserResponse:
        """
        Create a new user.

        Args:
            request_data_pydantic: User creation data
            command: Injected CreateUserCommand

        Returns:
            CreateUserResponse with the created user ID

        Raises:
            UserAlreadyExistsError: When a user with the same email/username exists
            UserValidationError: When validation fails
        """
        request_data = CreateUserRequest(
            name=request_data_pydantic.name,
            email=request_data_pydantic.email,
            username=request_data_pydantic.username,
            keycloak_id=request_data_pydantic.keycloak_id,
        )
        return await command.execute(request_data)

    return router
