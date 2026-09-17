"""Unassign user from group command."""

from dataclasses import dataclass

from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class UnassignUserFromGroupCommand:
    """Unassign user from group command."""

    user_id: str
    group_id: str


async def handle_unassign_user_from_group(
    command: UnassignUserFromGroupCommand,
    keycloak_client: KeycloakClient,
) -> None:
    """
    Handle unassign user from group command.

    Args:
        command: Unassign user from group command
        keycloak_client: Keycloak client
    """
    await keycloak_client.unassign_user_from_group(
        user_id=command.user_id,
        group_id=command.group_id,
    )
