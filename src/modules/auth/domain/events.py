"""Keycloak events and sessions domain models."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class LoginEvent:
    """Login event data from Keycloak."""

    time: int  # Timestamp in milliseconds
    type: str  # LOGIN, LOGOUT, LOGIN_ERROR, etc.
    user_id: str
    client_id: str
    ip_address: str | None
    username: str | None
    details: dict[str, Any]

    @property
    def datetime(self) -> datetime:
        """Convert timestamp to datetime."""
        return datetime.fromtimestamp(self.time / 1000, tz=UTC)


@dataclass(frozen=True, slots=True)
class UserSession:
    """Active user session data."""

    id: str
    username: str
    user_id: str
    ip_address: str | None
    start: int  # Timestamp in milliseconds
    last_access: int  # Timestamp in milliseconds
    clients: dict[str, str]

    @property
    def start_datetime(self) -> datetime:
        """Convert start timestamp to datetime."""
        return datetime.fromtimestamp(self.start / 1000, tz=UTC)

    @property
    def last_access_datetime(self) -> datetime:
        """Convert last access timestamp to datetime."""
        return datetime.fromtimestamp(self.last_access / 1000, tz=UTC)
