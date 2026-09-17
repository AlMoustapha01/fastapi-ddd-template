"""Logout command."""

from dataclasses import dataclass

from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class LogoutCommand:
    """Logout command."""

    refresh_token: str


async def handle_logout(
    command: LogoutCommand,
    keycloak_client: KeycloakClient,
) -> None:
    """
    Handle logout command.

    Args:
        command: Logout command
        keycloak_client: Keycloak client
    """
    await keycloak_client.logout(refresh_token=command.refresh_token)
