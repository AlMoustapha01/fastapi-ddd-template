"""User management controllers."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from modules.auth.application.dependencies import require_roles
from modules.auth.application.queries import GetUserByIdQuery, handle_get_user_by_id
from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import KeycloakClient


class UserResponse(BaseModel):
    """User response."""

    model_config = ConfigDict(frozen=True)

    id: str
    username: str
    email: str | None
    first_name: str | None
    last_name: str | None
    enabled: bool
    email_verified: bool


def create_users_router() -> APIRouter:
    """Create users router."""
    router = APIRouter()

    @router.get(
        "/users/{user_id}",
        response_model=UserResponse,
        summary="Get user by ID",
        description="Get user information by ID (requires admin role)",
    )
    @inject
    async def get_user_by_id(
        user_id: str,
        keycloak_client: FromDishka[KeycloakClient],
        _: Annotated[AuthUser, Depends(require_roles(["perm_users_management"]))],
    ) -> UserResponse:
        """Get user by ID endpoint."""
        query = GetUserByIdQuery(user_id=user_id)
        user = await handle_get_user_by_id(query, keycloak_client)

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            enabled=user.enabled,
            email_verified=user.email_verified,
        )

    return router
