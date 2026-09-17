"""Make user active command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.users.domain.exceptions import UserNotFoundError
from modules.users.domain.ports import UserRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class MakeActiveUserRequest:
    id: UUID


class MakeActiveUserResponse(TypedDict):
    id: UUID


class MakeActiveUserCommand:
    """Command to activate a user."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repository = user_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: MakeActiveUserRequest) -> MakeActiveUserResponse:
        """
        Execute the make user active command.

        :param request: The request with user ID
        :return: Response with the user ID
        :raises UserNotFoundError: When user is not found
        """
        log.info("Activating user: %s", request.id)

        user = await self._user_repository.find_one_by_id(request.id)
        if not user:
            raise UserNotFoundError(f"User with ID {request.id} not found")

        user.make_active()

        await self._user_repository.save(user)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("User activated successfully: %s", user.id_.value)

        return MakeActiveUserResponse(id=user.id_.value)
