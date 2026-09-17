"""User repository implementation."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.db.repository import BaseRepository
from core.lib.db.repository.errors import EntityQueryError
from modules.users.domain.ports import UserRepositoryPort
from modules.users.domain.user import User
from modules.users.infrastructure.mappers import UserMapper
from modules.users.infrastructure.models.user_model import UserModel


class UserRepository(BaseRepository[User, UserModel], UserRepositoryPort):
    """Repository implementation for User entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            model=UserModel,
            mapper=UserMapper(),
        )

    async def find_one_by_email(self, email: str) -> User | None:
        """Find a user by email address."""
        try:
            stmt = select(self.model).where(self.model.email == email)
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by email",
                cause=e,
                details={"email": email},
            ) from e

    async def find_one_by_username(self, username: str) -> User | None:
        """Find a user by username."""
        try:
            stmt = select(self.model).where(self.model.username == username)
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by username",
                cause=e,
                details={"username": username},
            ) from e

    async def find_one_by_keycloak_id(self, keycloak_id: str) -> User | None:
        """Find a user by Keycloak ID."""
        try:
            stmt = select(self.model).where(self.model.keycloak_id == keycloak_id)
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by keycloak_id",
                cause=e,
                details={"keycloak_id": keycloak_id},
            ) from e
