"""Create user command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.users.domain.exceptions import UserAlreadyExistsError
from modules.users.domain.ports import UserRepositoryPort
from modules.users.domain.user import CreateUserProps, User

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateUserRequest:
    name: str
    email: str
    username: str
    keycloak_id: str


class CreateUserResponse(TypedDict):
    id: UUID


class CreateUserCommand:
    """Command to create a new user."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repository = user_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateUserRequest) -> CreateUserResponse:
        """
        Execute the create user command.

        :param request: The user creation request
        :return: Response with the created user ID
        :raises UserAlreadyExistsError: When a user with the same email/username exists
        """
        log.info("Creating user: %s", request.username)

        # Check if user already exists
        existing_user = await self._user_repository.find_one_by_email(request.email)
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with email {request.email} already exists"
            )

        existing_user = await self._user_repository.find_one_by_username(
            request.username
        )
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with username {request.username} already exists"
            )

        existing_user = await self._user_repository.find_one_by_keycloak_id(
            request.keycloak_id
        )
        if existing_user:
            raise UserAlreadyExistsError(
                f"User with keycloak_id {request.keycloak_id} already exists"
            )

        user = User.create(
            props=CreateUserProps(
                name=request.name,
                email=request.email,
                username=request.username,
                keycloak_id=request.keycloak_id,
            )
        )

        await self._user_repository.add(user)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("User created successfully: %s", user.id_.value)

        return CreateUserResponse(id=user.id_.value)
