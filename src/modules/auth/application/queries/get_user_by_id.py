"""Get user by ID query."""

from dataclasses import dataclass

from modules.auth.domain import KeycloakUser
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass
class GetUserByIdQuery:
    """Get user by ID query."""

    user_id: str


async def handle_get_user_by_id(
    query: GetUserByIdQuery,
    keycloak_client: KeycloakClient,
) -> KeycloakUser:
    """
    Handle get user by ID query.

    Args:
        query: Get user by ID query
        keycloak_client: Keycloak client

    Returns:
        KeycloakUser
    """
    return await keycloak_client.get_user_by_id(user_id=query.user_id)
