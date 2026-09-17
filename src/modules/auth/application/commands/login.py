"""Login command."""

from dataclasses import dataclass

from modules.auth.domain import TokenResponse
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class LoginCommand:
    """Login command."""

    username: str
    password: str


async def handle_login(
    command: LoginCommand,
    keycloak_client: KeycloakClient,
) -> TokenResponse:
    """
    Handle login command.

    Args:
        command: Login command
        keycloak_client: Keycloak client

    Returns:
        TokenResponse with access and refresh tokens
    """
    return await keycloak_client.login(
        username=command.username,
        password=command.password,
    )
