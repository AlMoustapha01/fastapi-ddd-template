"""Authentication user domain model."""

from dataclasses import dataclass


@dataclass
class AuthUser:
    """Authenticated user from JWT token."""

    id: str
    username: str
    email: str | None = None
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    roles: list[str] | None = None

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        if not self.roles:
            return False
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        if not self.roles:
            return False
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all of the specified roles."""
        if not self.roles:
            return False
        return all(role in self.roles for role in roles)


@dataclass
class KeycloakUser:
    """Keycloak user from admin API."""

    id: str
    username: str
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    enabled: bool = True
    email_verified: bool = False
    created_timestamp: int | None = None


@dataclass
class KeycloakGroup:
    """Keycloak group from admin API."""

    id: str
    name: str
    path: str


@dataclass
class KeycloakRole:
    """Keycloak role from admin API."""

    id: str
    name: str
    description: str | None = None
    composite: bool = False
