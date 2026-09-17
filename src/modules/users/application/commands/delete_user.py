"""Delete user command."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from core.services.user_profile_service import KeycloakClientProtocol
from modules.users.domain.exceptions import UserNotFoundError
from modules.users.domain.ports import UserRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteUserRequest:
    id: UUID


class DeleteUserCommand:
    """Command to delete a user."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
        keycloak_client: KeycloakClientProtocol,
    ) -> None:
        self._user_repository = user_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager
        self._keycloak_client = keycloak_client

    async def execute(self, request: DeleteUserRequest) -> None:
        """
        Execute the delete user command.

        :param request: The user deletion request
        :raises UserNotFoundError: When user is not found
        """
        log.info("Deleting user: %s", request.id)

        user = await self._user_repository.find_one_by_id(request.id)
        if not user:
            raise UserNotFoundError(f"User with ID {request.id} not found")

        user_groups = await self._keycloak_client.get_user_groups(
            user_id=user.props.keycloak_id
        )
        for group in user_groups:
            log.info(
                "Unassigning user %s from group %s",
                user.props.keycloak_id,
                group.id,
            )
            await self._keycloak_client.unassign_user_from_group(
                user_id=user.props.keycloak_id,
                group_id=group.id,
            )

        await self._user_repository.delete(user)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("User deleted successfully: %s", request.id)
