"""Get user permissions (roles) controller."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from modules.auth.application.dependencies import get_current_user
from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import KeycloakClient


class RoleResponse(BaseModel):
    """Role response model."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    description: str | None = None
    composite: bool = False


class PermissionsResponse(BaseModel):
    """User permissions response."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    username: str
    roles: list[RoleResponse]


def create_permissions_router() -> APIRouter:
    """Create permissions router."""
    router = APIRouter()

    @router.get(
        "/me/permissions",
        response_model=PermissionsResponse,
        summary="Get current user permissions",
        description="Get realm roles (permissions) for the current authenticated user. \
        Only returns roles starting with 'perm_'",
    )
    @inject
    async def get_my_permissions(
        auth_user: Annotated[AuthUser, Depends(get_current_user)],
        keycloak_client: FromDishka[KeycloakClient],
    ) -> PermissionsResponse:
        """
        Get current user permissions endpoint.

        Returns only effective realm roles that start with 'perm_' prefix.
        This includes both directly assigned roles and roles from composite roles.
        """
        try:
            # Get all effective roles (including composite)
            effective_roles = await keycloak_client.get_user_effective_realm_roles(
                auth_user.id
            )

            # Filter roles that start with 'perm_'
            permission_roles = [
                role for role in effective_roles if role.name.startswith("perm_")
            ]

            return PermissionsResponse(
                user_id=auth_user.id,
                username=auth_user.username,
                roles=[
                    RoleResponse(
                        id=role.id,
                        name=role.name,
                        description=role.description,
                        composite=role.composite,
                    )
                    for role in permission_roles
                ],
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve user permissions: {e!s}",
            ) from e

    return router
