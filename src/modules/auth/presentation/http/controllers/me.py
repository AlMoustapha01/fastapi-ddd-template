"""Get current user controller."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from core.services import GroupData, UserProfileService
from modules.auth.application.dependencies import get_current_user
from modules.auth.domain import AuthUser


class UserResponse(BaseModel):
    """Enhanced user response with database and Keycloak data."""

    model_config = ConfigDict(frozen=True)

    # From database (User entity)
    id: str  # Database user ID
    name: str
    email: str
    username: str
    is_active: bool

    # From Keycloak JWT
    keycloak_id: str
    roles: list[str]

    # From Keycloak API
    groups: list[GroupData]


def create_me_router() -> APIRouter:
    """Create me router."""
    router = APIRouter()

    @router.get(
        "/me",
        response_model=UserResponse,
        summary="Get current user",
        description="Get current authenticated user with database info, \
        roles, and groups",
    )
    @inject
    async def get_me(
        auth_user: Annotated[AuthUser, Depends(get_current_user)],
        profile_service: FromDishka[UserProfileService],
    ) -> UserResponse:
        """
        Get current user endpoint.

        Combines data from:
        1. Database (User entity) - via Keycloak ID
        2. JWT token (roles)
        3. Keycloak API (groups)
        """
        # Get complete user profile using the service
        profile = await profile_service.get_user_profile(
            keycloak_id=auth_user.id,
            roles=auth_user.roles or [],
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with Keycloak ID {auth_user.id} not found in database",
            )

        return UserResponse(
            id=profile.id,
            name=profile.name,
            email=profile.email,
            username=profile.username,
            is_active=profile.is_active,
            keycloak_id=profile.keycloak_id,
            roles=profile.roles,
            groups=profile.groups,
        )

    return router
