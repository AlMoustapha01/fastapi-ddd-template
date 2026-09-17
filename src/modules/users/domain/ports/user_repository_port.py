from typing import Protocol

from core.lib.db.repository import BaseRepositoryPort
from modules.users.domain.user import User


class UserRepositoryPort(BaseRepositoryPort[User], Protocol):
    """Port interface for User persistence."""

    async def find_one_by_email(self, email: str) -> User | None:
        """Find a user by email address."""

    async def find_one_by_username(self, username: str) -> User | None:
        """Find a user by username."""

    async def find_one_by_keycloak_id(self, keycloak_id: str) -> User | None:
        """Find a user by Keycloak ID."""
