"""User login history controller."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from modules.auth.application.dependencies import get_current_user, require_roles
from modules.auth.application.queries import (
    GetUserLoginHistoryQuery,
    handle_get_user_login_history,
)
from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import KeycloakClient


class LoginEventResponse(BaseModel):
    """Response model for login event."""

    model_config = ConfigDict(frozen=True)

    time: int = Field(..., description="Event timestamp in milliseconds")
    datetime: str = Field(..., description="Event datetime in ISO format")
    type: str = Field(..., description="Event type (LOGIN, LOGOUT, etc.)")
    user_id: str = Field(..., description="Keycloak user ID")
    client_id: str = Field(..., description="Client ID")
    ip_address: str | None = Field(None, description="IP address")
    username: str | None = Field(None, description="Username")
    details: dict[str, str] = Field(
        default_factory=dict, description="Additional event details"
    )


def create_login_history_router() -> APIRouter:
    """Create login history router."""
    router = APIRouter()

    @router.get(
        "/users/me/login-history",
        response_model=list[LoginEventResponse],
        summary="Get my login history",
        description="Get login history for the current authenticated user",
    )
    @inject
    async def get_my_login_history(
        keycloak_client: FromDishka[KeycloakClient],
        current_user: Annotated[AuthUser, Depends(get_current_user)],
        max_results: Annotated[int, Query(ge=1, le=1000)] = 100,
    ) -> list[LoginEventResponse]:
        """
        Get current user's login history endpoint.

        Args:
            keycloak_client: Injected Keycloak client
            current_user: Current authenticated user
            max_results: Maximum number of events to return (1-1000)

        Returns:
            List of login events
        """
        query = GetUserLoginHistoryQuery(
            user_id=current_user.id, max_results=max_results
        )
        events = await handle_get_user_login_history(query, keycloak_client)

        return [
            LoginEventResponse(
                time=event.time,
                datetime=event.datetime.isoformat(),
                type=event.type,
                user_id=event.user_id,
                client_id=event.client_id,
                ip_address=event.ip_address,
                username=event.username,
                details=event.details,
            )
            for event in events
        ]

    @router.get(
        "/users/{user_id}/login-history",
        response_model=list[LoginEventResponse],
        summary="Get user login history",
        description="Get login history for a user from Keycloak events",
    )
    @inject
    async def get_user_login_history(
        user_id: str,
        keycloak_client: FromDishka[KeycloakClient],
        _current_user: Annotated[AuthUser, Depends(get_current_user)],
        _: Annotated[AuthUser, Depends(require_roles(["perm_users_management"]))],
        max_results: Annotated[int, Query(ge=1, le=1000)] = 100,
    ) -> list[LoginEventResponse]:
        """
        Get user login history endpoint.

        Args:
            user_id: Keycloak user ID
            keycloak_client: Injected Keycloak client
            _current_user: Current authenticated user
            _: Permission check (requires perm_users_management or admin)
            max_results: Maximum number of events to return (1-1000)

        Returns:
            List of login events

        Raises:
            404: User not found
            403: Insufficient permissions
        """
        query = GetUserLoginHistoryQuery(user_id=user_id, max_results=max_results)
        events = await handle_get_user_login_history(query, keycloak_client)

        return [
            LoginEventResponse(
                time=event.time,
                datetime=event.datetime.isoformat(),
                type=event.type,
                user_id=event.user_id,
                client_id=event.client_id,
                ip_address=event.ip_address,
                username=event.username,
                details=event.details,
            )
            for event in events
        ]

    return router
