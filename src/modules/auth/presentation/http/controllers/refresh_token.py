"""Refresh token controller."""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from modules.auth.application.commands import RefreshTokenCommand, handle_refresh_token
from modules.auth.infrastructure.keycloak import KeycloakClient


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    model_config = ConfigDict(frozen=True)

    refresh_token: str


class TokenResponse(BaseModel):
    """Token response."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str


def create_refresh_token_router() -> APIRouter:
    """Create refresh token router."""
    router = APIRouter()

    @router.post(
        "/refresh",
        response_model=TokenResponse,
        summary="Refresh token",
        description="Refresh access token using refresh token",
        status_code=200,
    )
    @inject
    async def refresh_token(
        request: RefreshTokenRequest,
        keycloak_client: FromDishka[KeycloakClient],
    ) -> TokenResponse:
        """Refresh token endpoint."""
        command = RefreshTokenCommand(refresh_token=request.refresh_token)
        token = await handle_refresh_token(command, keycloak_client)

        return TokenResponse(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_in=token.expires_in,
            refresh_expires_in=token.refresh_expires_in,
            token_type=token.token_type,
        )

    return router
