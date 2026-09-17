"""List groups query."""

from dataclasses import dataclass

from modules.auth.domain import KeycloakGroup
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class ListGroupsQuery:
    """List groups query."""

    pass


async def handle_list_groups(
    query: ListGroupsQuery,  # noqa: ARG001
    keycloak_client: KeycloakClient,
) -> list[KeycloakGroup]:
    """
    Handle list groups query.

    Args:
        query: List groups query
        keycloak_client: Keycloak client

    Returns:
        List of KeycloakGroup
    """
    return await keycloak_client.list_groups()
