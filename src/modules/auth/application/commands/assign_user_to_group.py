"""Assign user to group command."""

from dataclasses import dataclass

from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class AssignUserToGroupCommand:
    """Assign user to group command."""

    user_id: str
    group_id: str


async def handle_assign_user_to_group(
    command: AssignUserToGroupCommand,
    keycloak_client: KeycloakClient,
) -> None:
    """
    Handle assign user to group command.

    Args:
        command: Assign user to group command
        keycloak_client: Keycloak client
    """
    await keycloak_client.assign_user_to_group(
        user_id=command.user_id,
        group_id=command.group_id,
    )
