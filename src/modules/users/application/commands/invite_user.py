"""Invite user command - searches in Keycloak and creates in database."""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from core.services import KeycloakClientProtocol
from modules.users.domain.ports import UserRepositoryPort
from modules.users.domain.user import CreateUserProps, User

log = logging.getLogger(__name__)


class UserNotFoundInKeycloakError(Exception):
    """Raised when a user is not found in Keycloak."""

    def __init__(self, email: str | None = None, username: str | None = None) -> None:
        self.email = email
        self.username = username
        criteria = ", ".join(
            f"{k}={v}" for k, v in [("email", email), ("username", username)] if v
        )
        super().__init__(f"User not found in Keycloak with {criteria}")


class InvalidInviteRequestError(Exception):
    """Raised when the invite request is invalid."""

    def __init__(self) -> None:
        super().__init__("Either email or username must be provided")


@dataclass(frozen=True, slots=True, kw_only=True)
class InviteUserRequest:
    """Request to invite a user by email or username."""

    email: str | None = None
    username: str | None = None
    group_id: str | None = None

    def __post_init__(self) -> None:
        if not self.email and not self.username:
            raise InvalidInviteRequestError


@dataclass(frozen=True, slots=True)
class InviteUserResponse:
    """Response containing the created user ID and Keycloak info."""

    id: UUID
    keycloak_id: str
    name: str
    email: str
    username: str
    already_exists: bool
    group_id: str | None


class InviteUserCommand:
    """
    Command to invite a user.

    Searches for the user in Keycloak by email or username,
    then creates the user in the local database.
    """

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        keycloak_client: KeycloakClientProtocol,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._user_repository = user_repository
        self._keycloak_client = keycloak_client
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: InviteUserRequest) -> InviteUserResponse:
        """Execute the invite user command."""
        keycloak_user = await self._find_keycloak_user(request)
        existing_user = await self._user_repository.find_one_by_keycloak_id(
            keycloak_user.id
        )

        if existing_user:
            return await self._handle_existing_user(
                existing_user, keycloak_user, request
            )

        return await self._create_and_invite_user(keycloak_user, request)

    async def _find_keycloak_user(self, request: InviteUserRequest) -> Any:
        """Search for user in Keycloak."""
        log.info(
            "Searching user in Keycloak: email=%s, username=%s",
            request.email,
            request.username,
        )

        keycloak_users = await self._keycloak_client.search_users(
            email=request.email,
            username=request.username,
            exact=True,
        )

        if not keycloak_users:
            raise UserNotFoundInKeycloakError(
                email=request.email,
                username=request.username,
            )

        keycloak_user = keycloak_users[0]
        log.info(
            "Found user in Keycloak: id=%s, username=%s",
            keycloak_user.id,
            keycloak_user.username,
        )
        return keycloak_user

    async def _handle_existing_user(
        self,
        existing_user: User,
        keycloak_user: Any,
        request: InviteUserRequest,
    ) -> InviteUserResponse:
        """Handle case when user already exists in database."""
        log.info("User already exists in database: %s", existing_user.id_.value)

        await self._assign_to_group_if_needed(keycloak_user.id, request.group_id)

        return InviteUserResponse(
            id=existing_user.id_.value,
            keycloak_id=keycloak_user.id,
            name=existing_user.props.name,
            email=existing_user.props.email.value,
            username=existing_user.props.username,
            already_exists=True,
            group_id=request.group_id,
        )

    async def _create_and_invite_user(
        self,
        keycloak_user: Any,
        request: InviteUserRequest,
    ) -> InviteUserResponse:
        """Create a new user in the database."""
        full_name = self._build_full_name(keycloak_user)

        user = User.create(
            props=CreateUserProps(
                name=full_name,
                email=keycloak_user.email or "",
                username=keycloak_user.username,
                keycloak_id=keycloak_user.id,
            )
        )

        await self._user_repository.add(user)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            "User created successfully: id=%s, keycloak_id=%s",
            user.id_.value,
            keycloak_user.id,
        )

        await self._assign_to_group_if_needed(keycloak_user.id, request.group_id)

        return InviteUserResponse(
            id=user.id_.value,
            keycloak_id=keycloak_user.id,
            name=full_name,
            email=keycloak_user.email or "",
            username=keycloak_user.username,
            already_exists=False,
            group_id=request.group_id,
        )

    async def _assign_to_group_if_needed(
        self,
        user_id: str,
        group_id: str | None,
    ) -> None:
        """Assign user to Keycloak group if group_id is provided."""
        if not group_id:
            return

        try:
            await self._keycloak_client.assign_user_to_group(
                user_id=user_id,
                group_id=group_id,
            )
            log.info("User %s assigned to group %s", user_id, group_id)
        except Exception:
            log.exception("Failed to assign user %s to group %s", user_id, group_id)

    @staticmethod
    def _build_full_name(keycloak_user: Any) -> str:
        """Build full name from Keycloak user data."""
        name_parts = filter(None, [keycloak_user.first_name, keycloak_user.last_name])
        return " ".join(name_parts) or keycloak_user.username
