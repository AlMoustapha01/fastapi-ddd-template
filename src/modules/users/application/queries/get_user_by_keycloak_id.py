"""Get user by Keycloak ID query."""

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

from modules.users.domain.exceptions import UserNotFoundError
from modules.users.domain.ports import UserRepositoryPort


@dataclass(frozen=True)
class GetUserByKeycloakIdRequest:
    """Request to get user by Keycloak ID."""

    keycloak_id: str


class UserByKeycloakIdResponse(BaseModel):
    """Response for get user by Keycloak ID query."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    username: str
    keycloak_id: str
    is_active: bool


class GetUserByKeycloakIdQuery:
    """Query to get user by Keycloak ID."""

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        """Initialize query."""
        self.user_repository = user_repository

    async def execute(
        self, request: GetUserByKeycloakIdRequest
    ) -> UserByKeycloakIdResponse:
        """
        Execute query to get user by Keycloak ID.

        Args:
            request: Request with Keycloak ID

        Returns:
            UserByKeycloakIdResponse with user details

        Raises:
            UserNotFoundError: When user is not found
        """
        user = await self.user_repository.find_one_by_keycloak_id(request.keycloak_id)

        if not user:
            raise UserNotFoundError(
                f"User with Keycloak ID {request.keycloak_id} not found"
            )

        return UserByKeycloakIdResponse(
            id=str(user.id_.value),
            name=user.props.name,
            email=str(user.props.email.value),
            username=user.props.username,
            keycloak_id=user.props.keycloak_id,
            is_active=user.props.is_active,
        )
