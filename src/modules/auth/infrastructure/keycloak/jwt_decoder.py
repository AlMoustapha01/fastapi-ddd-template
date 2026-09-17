"""JWT token decoder."""

import logging
from typing import Any

from jose import JWTError, jwt

from core.config.keycloak import KeycloakSettings
from modules.auth.domain import AuthUser

log = logging.getLogger(__name__)


class JWTDecoder:
    """JWT token decoder for Keycloak tokens."""

    def __init__(self, keycloak: KeycloakSettings) -> None:
        """Initialize JWT decoder."""
        self.keycloak = keycloak
        self.public_key = self._format_public_key(keycloak.public_key)

    def _format_public_key(self, key: str) -> str:
        """Format public key with PEM headers if not present."""
        if key.startswith("-----BEGIN"):
            return key
        return f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate JWT token."""

        if not self.public_key:
            raise JWTError("Public key not configured")

        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                audience=self.keycloak.client_id,
            )
            log.debug("Token decoded for user: %s", payload.get("sub"))
            return payload
        except JWTError as err:
            log.warning("Failed to decode token: %s", err)
            raise

    def extract_user(self, token: str) -> AuthUser:
        """Extract user from JWT token."""
        payload = self.decode_token(token)
        return AuthUser(
            id=payload.get("sub", ""),
            username=payload.get("preferred_username", ""),
            email=payload.get("email"),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
            roles=self._extract_roles(payload),
        )

    def _extract_roles(self, payload: dict[str, Any]) -> list[str]:
        """Extract roles from JWT payload."""
        roles: list[str] = []

        # Realm roles
        realm_access = payload.get("realm_access", {})
        if isinstance(realm_access, dict):
            realm_roles = realm_access.get("roles", [])
            if isinstance(realm_roles, list):
                roles.extend(realm_roles)

        # Client roles
        resource_access = payload.get("resource_access", {})
        if isinstance(resource_access, dict):
            for resource_data in resource_access.values():
                if isinstance(resource_data, dict):
                    resource_roles = resource_data.get("roles", [])
                    if isinstance(resource_roles, list):
                        roles.extend(resource_roles)

        return roles
