"""Get user by ID query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from modules.users.domain.exceptions import UserNotFoundError
from modules.users.domain.ports import UserRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetUserByIdRequest:
    """Request to get a user by ID."""

    id: UUID


class UserDetailResponse(TypedDict):
    """Detailed user response."""

    id: UUID
    name: str
    email: str
    username: str
    keycloak_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class GetUserByIdQuery:
    """Query to get a user by ID."""

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._user_repository = user_repository

    async def execute(self, request: GetUserByIdRequest) -> UserDetailResponse:
        """
        Execute the get user by ID query.

        :param request: The request with user ID
        :return: User detail response
        :raises UserNotFoundError: When user is not found
        """
        log.info("Fetching user by ID: %s", request.id)

        user = await self._user_repository.find_one_by_id(request.id)
        if not user:
            raise UserNotFoundError(f"User with ID {request.id} not found")

        log.info("User found: %s", user.props.username)

        return UserDetailResponse(
            id=user.id_.value,
            name=user.props.name,
            email=user.props.email.value,
            username=user.props.username,
            keycloak_id=user.props.keycloak_id,
            is_active=user.props.is_active,
            created_at=user.created_at_,
            updated_at=user.updated_at_,
        )
