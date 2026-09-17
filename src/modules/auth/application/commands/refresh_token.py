"""Refresh token command."""

from dataclasses import dataclass

from modules.auth.domain import TokenResponse
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class RefreshTokenCommand:
    """Refresh token command."""

    refresh_token: str


async def handle_refresh_token(
    command: RefreshTokenCommand,
    keycloak_client: KeycloakClient,
) -> TokenResponse:
    """
    Handle refresh token command.

    Args:
        command: Refresh token command
        keycloak_client: Keycloak client

    Returns:
        TokenResponse with new tokens
    """
    return await keycloak_client.refresh_token(refresh_token=command.refresh_token)
