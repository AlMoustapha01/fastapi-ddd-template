"""User profile service - orchestrates auth and users modules."""

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict


class UserProfileData(BaseModel):
    """User profile data combining auth and user info."""

    model_config = ConfigDict(frozen=True)

    # Database user info
    id: str
    name: str
    email: str
    username: str
    is_active: bool
    keycloak_id: str

    # Auth info
    roles: list[str]
    groups: list["GroupData"]


class GroupData(BaseModel):
    """Group data."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    path: str


class UserRepositoryProtocol(Protocol):
    """Protocol for user repository."""

    async def find_one_by_keycloak_id(self, keycloak_id: str) -> Any:
        """Find user by Keycloak ID."""
        ...


class KeycloakClientProtocol(Protocol):
    """Protocol for Keycloak client."""

    async def get_user_groups(self, user_id: str) -> list[Any]:
        """Get user groups."""
        ...

    async def search_users(
        self,
        email: str | None = None,
        username: str | None = None,
        exact: bool = True,
    ) -> list[Any]:
        """Search for users in Keycloak."""
        ...

    async def get_user_login_events(
        self,
        user_id: str,
        event_types: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        first: int = 0,
        max_results: int = 100,
    ) -> list[Any]:
        """Get user login events."""
        ...

    async def get_user_active_sessions(
        self,
        user_id: str,
    ) -> list[Any]:
        """Get active sessions for a user."""
        ...

    async def get_user_realm_roles(self, user_id: str) -> list[Any]:
        """Get user realm roles."""
        ...

    async def get_user_effective_realm_roles(self, user_id: str) -> list[Any]:
        """Get user effective realm roles."""
        ...

    async def assign_user_to_group(self, user_id: str, group_id: str) -> None:
        """Assign user to group."""
        ...

    async def unassign_user_from_group(self, user_id: str, group_id: str) -> None:
        """Unassign user from group."""
        ...

    async def list_groups(self) -> list[Any]:
        """List all groups."""
        ...


class UserProfileService:
    """Service to get complete user profile."""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        keycloak_client: KeycloakClientProtocol,
    ) -> None:
        """Initialize service."""
        self.user_repository = user_repository
        self.keycloak_client = keycloak_client

    async def get_user_profile(
        self, keycloak_id: str, roles: list[str]
    ) -> UserProfileData | None:
        """
        Get complete user profile.

        Args:
            keycloak_id: Keycloak user ID
            roles: User roles from JWT

        Returns:
            UserProfileData or None if user not found
        """
        # Get user from database
        user = await self.user_repository.find_one_by_keycloak_id(keycloak_id)
        if not user:
            return None

        # Get groups from Keycloak
        try:
            keycloak_groups = await self.keycloak_client.get_user_groups(keycloak_id)
            groups = [
                GroupData(
                    id=group.id,
                    name=group.name,
                    path=group.path,
                )
                for group in keycloak_groups
            ]
        except Exception:
            groups = []

        return UserProfileData(
            id=str(user.id_.value),
            name=user.props.name,
            email=str(user.props.email.value),
            username=user.props.username,
            is_active=user.props.is_active,
            keycloak_id=user.props.keycloak_id,
            roles=roles,
            groups=groups,
        )
