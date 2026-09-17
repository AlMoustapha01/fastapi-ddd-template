"""Invite user HTTP controller."""

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
    InviteUserCommand,
    InviteUserRequest,
)
from modules.users.domain.exceptions import UserValidationError


class InviteUserRequestPydantic(BaseModel):
    """
    Pydantic model for invite user request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    email: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="User email address to search in Keycloak",
    )
    username: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Username to search in Keycloak",
    )
    group_id: str | None = Field(
        None,
        description="Keycloak group ID to assign the user to",
    )


class InviteUserResponsePydantic(BaseModel):
    """Response model for invite user endpoint."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="User ID in local database")
    keycloak_id: str = Field(..., description="Keycloak user identifier")
    name: str = Field(..., description="User full name")
    email: str = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    already_exists: bool = Field(
        ...,
        description="True if user already existed in database, False if newly created",
    )
    group_id: str | None = Field(
        None,
        description="Keycloak group ID the user was assigned to",
    )


def create_invite_user_router() -> APIRouter:
    """Create router for user invitation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/invite",
        description=getdoc(InviteUserCommand),
        error_map={
            ValueError: rule(
                status=status.HTTP_400_BAD_REQUEST,
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
        status_code=status.HTTP_201_CREATED,
        response_model=InviteUserResponsePydantic,
    )
    @inject
    async def invite_user(
        request_data_pydantic: InviteUserRequestPydantic,
        command: FromDishka[InviteUserCommand],
        _: Annotated[
            AuthUser,
            Depends(require_roles(["perm_invite_user", "perm_users_management"])),
        ],
    ) -> InviteUserResponsePydantic:
        """
        Invite a user by searching in Keycloak and creating in local database.

        This endpoint searches for a user in Keycloak by email or username,
        then creates the user in the local database if they don't already exist.
        Optionally assigns the user to a Keycloak group.

        Args:
            request_data_pydantic: Email, username, and optional group_id
            command: Injected InviteUserCommand
            _: Current authenticated user (required)

        Returns:
            InviteUserResponsePydantic with user information, creation status,
                and group assignment

        Raises:
            ValueError: When neither email nor username is provided, or user not found
            UserValidationError: When validation fails
        """
        request_data = InviteUserRequest(
            email=request_data_pydantic.email,
            username=request_data_pydantic.username,
            group_id=request_data_pydantic.group_id,
        )
        response = await command.execute(request_data)

        return InviteUserResponsePydantic(
            id=str(response.id),
            keycloak_id=response.keycloak_id,
            name=response.name,
            email=response.email,
            username=response.username,
            already_exists=response.already_exists,
            group_id=response.group_id,
        )

    return router
