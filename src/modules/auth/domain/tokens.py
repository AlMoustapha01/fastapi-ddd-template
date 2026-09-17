"""Token domain models."""

from dataclasses import dataclass


@dataclass
class TokenResponse:
    """OAuth2 token response from Keycloak."""

    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str = "Bearer"  # noqa: S105
    scope: str | None = None


@dataclass
class LoginRequest:
    """Login request credentials."""

    username: str
    password: str


@dataclass
class RefreshTokenRequest:
    """Refresh token request."""

    refresh_token: str
