"""Login controller."""

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from modules.auth.application.commands import LoginCommand, handle_login
from modules.auth.infrastructure.keycloak import KeycloakClient


class LoginRequest(BaseModel):
    """Login request."""

    model_config = ConfigDict(frozen=True)

    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str


def create_login_router() -> APIRouter:
    """Create login router."""
    router = APIRouter()

    @router.post(
        "/login",
        response_model=TokenResponse,
        summary="Login",
        description="Login with username and password",
        status_code=200,
    )
    @inject
    async def login(
        request: LoginRequest,
        keycloak_client: FromDishka[KeycloakClient],
    ) -> TokenResponse:
        """Login endpoint."""
        command = LoginCommand(username=request.username, password=request.password)
        token = await handle_login(command, keycloak_client)

        return TokenResponse(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_in=token.expires_in,
            refresh_expires_in=token.refresh_expires_in,
            token_type=token.token_type,
        )

    return router
