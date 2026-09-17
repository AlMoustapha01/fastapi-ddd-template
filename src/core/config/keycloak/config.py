from typing import Final

from pydantic import BaseModel, Field

PORT_MIN: Final[int] = 1
PORT_MAX: Final[int] = 65535


class KeycloakSettings(BaseModel):
    """
    Keycloak OAuth2/OpenID Connect configuration.

    Maps to [kc_app] section in TOML files.
    Used for OAuth2 authentication flow with Keycloak.
    """

    # Client configuration
    server_url: str = Field(alias="SERVER_URL")  # Keycloak server URL
    realm: str = Field(alias="REALM")  # Keycloak realm name
    client_id: str = Field(alias="CLIENT_ID")  # OAuth2 client ID
    client_secret: str = Field(alias="CLIENT_SECRET")  # From .secrets.toml
    public_key: str = Field(alias="PUBLIC_KEY")  # RSA public key for JWT validation

    # OAuth2 endpoints (relative paths)
    authorization_endpoint: str = Field(alias="AUTHORIZATION_ENDPOINT")
    token_endpoint: str = Field(alias="TOKEN_ENDPOINT")
    userinfo_endpoint: str = Field(alias="USERINFO_ENDPOINT")
    jwks_endpoint: str = Field(alias="JWKS_ENDPOINT")
    logout_endpoint: str = Field(alias="LOGOUT_ENDPOINT")

    # Scopes
    scopes: str = Field(alias="SCOPES")  # Space-separated scopes

    def get_realm_url(self) -> str:
        """
        Get the full realm URL.

        Returns:
            Full realm URL (e.g., "http://localhost:8080/realms/eq-prepaid")
        """
        return f"{self.server_url}/realms/{self.realm}"

    def get_authorization_url(self) -> str:
        """
        Get the full authorization URL.

        Returns:
            Full authorization URL for OAuth2 flow
        """
        realm_url = self.get_realm_url()
        return f"{realm_url}{self.authorization_endpoint}"

    def get_token_url(self) -> str:
        """
        Get the full token URL.

        Returns:
            Full token URL for OAuth2 flow
        """
        realm_url = self.get_realm_url()
        return f"{realm_url}{self.token_endpoint}"

    def get_userinfo_url(self) -> str:
        """
        Get the full userinfo URL.

        Returns:
            Full userinfo URL for getting user details
        """
        realm_url = self.get_realm_url()
        return f"{realm_url}{self.userinfo_endpoint}"

    def get_jwks_url(self) -> str:
        """
        Get the full JWKS URL.

        Returns:
            Full JWKS URL for token validation
        """
        realm_url = self.get_realm_url()
        return f"{realm_url}{self.jwks_endpoint}"

    def get_logout_url(self) -> str:
        """
        Get the full logout URL.

        Returns:
            Full logout URL
        """
        realm_url = self.get_realm_url()
        return f"{realm_url}{self.logout_endpoint}"

    def get_scopes_list(self) -> list[str]:
        """
        Get scopes as a list.

        Returns:
            List of OAuth2 scopes
        """
        return self.scopes.split()

    def get_scopes_dict(self) -> dict[str, str]:
        """
        Get scopes as a dictionary for FastAPI OAuth2.

        Returns:
            Dictionary mapping scope names to descriptions
        """
        scopes_list = self.get_scopes_list()
        return {scope: f"{scope.capitalize()} scope" for scope in scopes_list}


class KeycloakAdminSettings(BaseModel):
    """
    Keycloak admin user settings.

    This class maps to the [kc_admin] section in .secrets.toml:
    - config/local/.secrets.toml: Contains admin credentials

    Mapping from .secrets.toml [kc_admin] section:
        USER="admin"      -> user: str
        PASSWORD="admin"  -> password: str

    These credentials are used to authenticate with Keycloak's admin API
    for administrative operations like creating realms, clients, and users.
    """

    user: str = Field(alias="USER")  # Admin username: "admin"
    password: str = Field(alias="PASSWORD")  # Admin password: "admin"
