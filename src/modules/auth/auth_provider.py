"""Dishka provider for auth module."""

from dishka import Provider, Scope, provide

from core.config.keycloak import KeycloakAdminSettings, KeycloakSettings
from core.services import KeycloakClientProtocol
from modules.auth.infrastructure.keycloak import JWTDecoder, KeycloakClient


class AuthProvider(Provider):
    """Provider for auth dependencies."""

    scope = Scope.REQUEST

    @provide
    def jwt_decoder(self, keycloak: KeycloakSettings) -> JWTDecoder:
        """Provide JWT decoder."""
        return JWTDecoder(keycloak=keycloak)

    @provide
    def keycloak_client(
        self,
        keycloak: KeycloakSettings,
        admin_settings: KeycloakAdminSettings,
    ) -> KeycloakClient:
        """Provide Keycloak client."""
        return KeycloakClient(keycloak=keycloak, admin_settings=admin_settings)

    @provide
    def keycloak_client_protocol(
        self,
        client: KeycloakClient,
    ) -> KeycloakClientProtocol:
        """Provide KeycloakClientProtocol for core services."""
        return client
