"""Logout controller."""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from modules.auth.application.commands import LogoutCommand, handle_logout
from modules.auth.infrastructure.keycloak import KeycloakClient


class LogoutRequest(BaseModel):
    """Logout request."""

    model_config = ConfigDict(frozen=True)

    refresh_token: str


def create_logout_router() -> APIRouter:
    """Create logout router."""
    router = APIRouter()

    @router.post(
        "/logout",
        summary="Logout",
        description="Logout and revoke refresh token",
        status_code=204,
    )
    @inject
    async def logout(
        request: LogoutRequest,
        keycloak_client: FromDishka[KeycloakClient],
    ) -> None:
        """Logout endpoint."""
        command = LogoutCommand(refresh_token=request.refresh_token)
        await handle_logout(command, keycloak_client)

    return router
