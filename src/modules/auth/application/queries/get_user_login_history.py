"""Query to get user login history from Keycloak."""

from dataclasses import dataclass

from modules.auth.domain import LoginEvent
from modules.auth.infrastructure.keycloak import KeycloakClient


@dataclass(frozen=True)
class GetUserLoginHistoryQuery:
    """Query to get user login history."""

    user_id: str
    max_results: int = 100


async def handle_get_user_login_history(
    query: GetUserLoginHistoryQuery,
    keycloak_client: KeycloakClient,
) -> list[LoginEvent]:
    """
    Handle get user login history query.

    Args:
        query: Query parameters
        keycloak_client: Keycloak client

    Returns:
        List of login events

    Raises:
        ValueError: If user not found
        httpx.HTTPError: If Keycloak API fails
    """
    return await keycloak_client.get_user_login_events(
        user_id=query.user_id,
        max_results=query.max_results,
    )
