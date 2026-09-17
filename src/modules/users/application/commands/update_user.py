"""Update user command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.users.domain.exceptions import UserAlreadyExistsError, UserNotFoundError
from modules.users.domain.ports import UserRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateUserRequest:
    id: UUID
    name: str | None = None
    email: str | None = None
    username: str | None = None


class UpdateUserResponse(TypedDict):
    id: UUID


class UpdateUserCommand:
    """Command to update user details."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repository = user_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateUserRequest) -> UpdateUserResponse:
        """
        Execute the update user command.

        :param request: The user update request
        :return: Response with the updated user ID
        :raises UserNotFoundError: When user is not found
        :raises UserAlreadyExistsError: When email/username already exists
        """
        log.info("Updating user: %s", request.id)

        user = await self._user_repository.find_one_by_id(request.id)
        if not user:
            raise UserNotFoundError(f"User with ID {request.id} not found")

        # Update fields if provided
        if request.name is not None:
            user.update_name(request.name)

        if request.email is not None:
            # Check if email already exists for another user
            existing_user = await self._user_repository.find_one_by_email(request.email)
            if existing_user and existing_user.id_.value != request.id:
                raise UserAlreadyExistsError(
                    f"User with email {request.email} already exists"
                )
            user.update_email(request.email)

        if request.username is not None:
            # Check if username already exists for another user
            existing_user = await self._user_repository.find_one_by_username(
                request.username
            )
            if existing_user and existing_user.id_.value != request.id:
                raise UserAlreadyExistsError(
                    f"User with username {request.username} already exists"
                )
            user.update_username(request.username)

        await self._user_repository.save(user)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("User updated successfully: %s", user.id_.value)

        return UpdateUserResponse(id=user.id_.value)
