"""Move user to group command."""

from dataclasses import dataclass

from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class MoveUserToGroupCommand:
    """Move user to group command."""

    user_id: str
    old_group_id: str
    new_group_id: str


async def handle_move_user_to_group(
    command: MoveUserToGroupCommand,
    keycloak_client: KeycloakClient,
) -> None:
    """
    Handle move user to group command.

    Args:
        command: Move user to group command
        keycloak_client: Keycloak client
    """
    await keycloak_client.unassign_user_from_group(
        user_id=command.user_id,
        group_id=command.old_group_id,
    )
    await keycloak_client.assign_user_to_group(
        user_id=command.user_id,
        group_id=command.new_group_id,
    )
