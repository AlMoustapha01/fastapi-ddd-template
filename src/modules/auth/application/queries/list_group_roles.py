"""List group roles query."""

from dataclasses import dataclass

from modules.auth.domain import KeycloakRole
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class ListGroupRolesQuery:
    """List group roles query."""

    group_id: str


async def handle_list_group_roles(
    query: ListGroupRolesQuery,
    keycloak_client: KeycloakClient,
) -> list[KeycloakRole]:
    """
    Handle list group roles query.

    Args:
        query: List group roles query
        keycloak_client: Keycloak client

    Returns:
        List of KeycloakRole
    """
    return await keycloak_client.list_group_roles(group_id=query.group_id)
