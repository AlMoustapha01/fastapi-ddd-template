"""Keycloak API client."""

import logging
from typing import Any

import httpx

from core.config.keycloak import KeycloakAdminSettings, KeycloakSettings
from modules.auth.domain import (
    KeycloakGroup,
    KeycloakRole,
    KeycloakUser,
    LoginEvent,
    TokenResponse,
    UserSession,
)

log = logging.getLogger(__name__)


class KeycloakClient:
    """Client for Keycloak Admin and Auth APIs."""

    def __init__(
        self,
        keycloak: KeycloakSettings,
        admin_settings: KeycloakAdminSettings,
    ) -> None:
        """
        Initialize Keycloak client.

        Args:
            keycloak: Keycloak configuration
            admin_settings: Admin credentials
        """
        self.keycloak = keycloak
        self.admin_settings = admin_settings
        self.base_url = keycloak.server_url
        self.realm = keycloak.realm
        self.client_id = keycloak.client_id
        self.client_secret = keycloak.client_secret
        self._admin_token: str | None = None

    async def _get_admin_token(self) -> str:
        """Get admin access token."""
        if self._admin_token:
            return self._admin_token

        url = f"{self.base_url}/realms/master{self.keycloak.token_endpoint}"
        data = {
            "client_id": "admin-cli",
            "username": self.admin_settings.user,
            "password": self.admin_settings.password,
            "grant_type": "password",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self._admin_token = token_data["access_token"]
            return self._admin_token

    async def login(self, username: str, password: str) -> TokenResponse:
        """
        Login user and get tokens.

        Args:
            username: Username
            password: Password

        Returns:
            TokenResponse with access and refresh tokens
        """
        url = f"{self.base_url}/realms/{self.realm}{self.keycloak.token_endpoint}"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
            "grant_type": "password",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
            refresh_expires_in=token_data["refresh_expires_in"],
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            TokenResponse with new tokens
        """
        url = f"{self.base_url}/realms/{self.realm}{self.keycloak.token_endpoint}"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()

        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"],
            refresh_expires_in=token_data["refresh_expires_in"],
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope"),
        )

    async def logout(self, refresh_token: str) -> None:
        """
        Logout user (revoke refresh token).

        Args:
            refresh_token: Refresh token to revoke
        """
        url = f"{self.base_url}/realms/{self.realm}{self.keycloak.logout_endpoint}"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()

    async def get_user_by_id(self, user_id: str) -> KeycloakUser:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            KeycloakUser
        """
        token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()

        return self._parse_user(user_data)

    async def get_user_groups(self, user_id: str) -> list[KeycloakGroup]:
        """
        Get groups for a user.

        Args:
            user_id: User ID

        Returns:
            List of KeycloakGroup
        """
        token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/groups"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            groups_data = response.json()

        return [self._parse_group(group) for group in groups_data]

    async def list_groups(self) -> list[KeycloakGroup]:
        """
        List all groups.

        Returns:
            List of KeycloakGroup
        """
        token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/groups"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            groups_data = response.json()

        return [self._parse_group(group) for group in groups_data]

    async def list_group_roles(self, group_id: str) -> list[KeycloakRole]:
        """
        List roles for a group.

        Args:
            group_id: Group ID

        Returns:
            List of KeycloakRole
        """
        token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/groups/"
            f"{group_id}/role-mappings/realm"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            roles_data = response.json()

        return [self._parse_role(role) for role in roles_data]

    async def get_user_realm_roles(self, user_id: str) -> list[KeycloakRole]:
        """
        Get realm roles directly assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of KeycloakRole directly assigned to the user

        Example:
            roles = await client.get_user_realm_roles("abc-123")
            for role in roles:
                print(f"{role.name}: {role.description}")
        """
        token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users/"
            f"{user_id}/role-mappings/realm"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            roles_data = response.json()

        return [self._parse_role(role) for role in roles_data]

    async def get_user_effective_realm_roles(self, user_id: str) -> list[KeycloakRole]:
        """
        Get all effective realm roles for a user (including composite roles).

        Args:
            user_id: User ID

        Returns:
            List of all effective KeycloakRole (including roles from composite roles)

        Example:
            roles = await client.get_user_effective_realm_roles("abc-123")
            for role in roles:
                print(f"{role.name}: {role.description}")
        """
        token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users/"
            f"{user_id}/role-mappings/realm/composite"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            roles_data = response.json()

        return [self._parse_role(role) for role in roles_data]

    async def get_user_available_realm_roles(self, user_id: str) -> list[KeycloakRole]:
        """
        Get available realm roles that can be assigned to a user.

        Args:
            user_id: User ID

        Returns:
            List of KeycloakRole available but not yet assigned to the user

        Example:
            roles = await client.get_user_available_realm_roles("abc-123")
            for role in roles:
                print(f"Available: {role.name}")
        """
        token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users/"
            f"{user_id}/role-mappings/realm/available"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            roles_data = response.json()

        return [self._parse_role(role) for role in roles_data]

    async def assign_user_to_group(self, user_id: str, group_id: str) -> None:
        """
        Assign user to group.

        Args:
            user_id: User ID
            group_id: Group ID
        """
        token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users/"
            f"{user_id}/groups/{group_id}"
        )
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient() as client:
            response = await client.put(url, headers=headers)
            response.raise_for_status()

    async def unassign_user_from_group(self, user_id: str, group_id: str) -> None:
        """
        Remove user from group.

        Args:
            user_id: User ID
            group_id: Group ID
        """
        admin_token = await self._get_admin_token()
        url = (
            f"{self.base_url}/admin/realms/{self.realm}/users/"
            f"{user_id}/groups/{group_id}"
        )
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()

    async def search_users(
        self,
        email: str | None = None,
        username: str | None = None,
        exact: bool = True,
    ) -> list[KeycloakUser]:
        """
        Search for users in Keycloak by email or username.

        Args:
            email: Email to search for
            username: Username to search for
            exact: If True, performs exact match; if False, performs partial match

        Returns:
            List of matching users

        Raises:
            ValueError: If neither email nor username is provided
        """
        if not email and not username:
            raise ValueError("Either email or username must be provided")

        admin_token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/users"
        headers = {"Authorization": f"Bearer {admin_token}"}

        params: dict[str, str | bool] = {"exact": exact}
        if email:
            params["email"] = email
        if username:
            params["username"] = username

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            users_data = response.json()

        return [self._parse_user(user) for user in users_data]

    def _parse_user(self, data: dict[str, Any]) -> KeycloakUser:
        """Parse user data from Keycloak API."""
        return KeycloakUser(
            id=data["id"],
            username=data["username"],
            email=data.get("email"),
            first_name=data.get("firstName"),
            last_name=data.get("lastName"),
            enabled=data.get("enabled", True),
            email_verified=data.get("emailVerified", False),
            created_timestamp=data.get("createdTimestamp"),
        )

    def _parse_group(self, data: dict[str, Any]) -> KeycloakGroup:
        """Parse group data from Keycloak API."""
        return KeycloakGroup(
            id=data["id"],
            name=data["name"],
            path=data["path"],
        )

    def _parse_role(self, data: dict[str, Any]) -> KeycloakRole:
        """Parse role data from Keycloak API."""
        return KeycloakRole(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            composite=data.get("composite", False),
        )

    async def get_user_login_events(
        self,
        user_id: str,
        event_types: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        first: int = 0,
        max_results: int = 100,
    ) -> list[LoginEvent]:
        """
        Get user login events from Keycloak.

        Args:
            user_id: Keycloak user ID
            event_types: List of event types (e.g., ["LOGIN", "LOGOUT", "LOGIN_ERROR"])
            date_from: Start date in format yyyy-MM-dd
            date_to: End date in format yyyy-MM-dd
            first: First result index (pagination)
            max_results: Maximum number of results (default: 100)

        Returns:
            List of login events

        Example:
            events = await client.get_user_login_events(
                user_id="abc-123",
                event_types=["LOGIN"],
                date_from="2024-01-01",
                max_results=50
            )

        Note:
            Requires Keycloak event logging to be enabled in realm settings.
            Events are stored for a limited time based on realm configuration.
        """
        admin_token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/events"
        headers = {"Authorization": f"Bearer {admin_token}"}

        params: dict[str, Any] = {
            "user": user_id,
            "first": first,
            "max": max_results,
        }

        if event_types:
            # Keycloak accepts multiple type parameters
            params["type"] = event_types

        if date_from:
            params["dateFrom"] = date_from

        if date_to:
            params["dateTo"] = date_to

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            events_data = response.json()

        return [self._parse_event(event) for event in events_data]

    async def get_user_active_sessions(
        self,
        user_id: str,
    ) -> list[UserSession]:
        """
        Get active sessions for a user.

        Args:
            user_id: Keycloak user ID

        Returns:
            List of active sessions

        Example:
            sessions = await client.get_user_active_sessions("abc-123")
            for session in sessions:
                print(f"Session from {session.ip_address}")
                print(f"Started: {session.start_datetime}")
        """
        admin_token = await self._get_admin_token()
        url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/sessions"
        headers = {"Authorization": f"Bearer {admin_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            sessions_data = response.json()

        return [self._parse_session(session) for session in sessions_data]

    def _parse_event(self, data: dict[str, Any]) -> LoginEvent:
        """Parse event data from Keycloak API."""
        return LoginEvent(
            time=data["time"],
            type=data["type"],
            user_id=data["userId"],
            client_id=data.get("clientId", ""),
            ip_address=data.get("ipAddress"),
            username=data.get("details", {}).get("username"),
            details=data.get("details", {}),
        )

    def _parse_session(self, data: dict[str, Any]) -> UserSession:
        """Parse session data from Keycloak API."""
        return UserSession(
            id=data["id"],
            username=data["username"],
            user_id=data["userId"],
            ip_address=data.get("ipAddress"),
            start=data["start"],
            last_access=data["lastAccess"],
            clients=data.get("clients", {}),
        )
