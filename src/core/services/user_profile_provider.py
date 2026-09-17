"""Provider for user profile service."""

from dishka import Provider, Scope, provide

from core.services.user_profile_service import (
    KeycloakClientProtocol,
    UserProfileService,
    UserRepositoryProtocol,
)


class UserProfileProvider(Provider):
    """Provider for user profile service."""

    scope = Scope.REQUEST

    @provide
    def provide_user_profile_service(
        self,
        user_repository: UserRepositoryProtocol,
        keycloak_client: KeycloakClientProtocol,
    ) -> UserProfileService:
        """Provide user profile service."""
        return UserProfileService(
            user_repository=user_repository,
            keycloak_client=keycloak_client,
        )
