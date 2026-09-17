"""OAuth2 security utilities for Keycloak integration."""

from fastapi.security import OAuth2AuthorizationCodeBearer

from core.config.keycloak import KeycloakSettings


def create_oauth2_scheme(
    keycloak: KeycloakSettings,
) -> OAuth2AuthorizationCodeBearer:
    """
    Create OAuth2 authorization code bearer scheme for Keycloak.

    This creates the FastAPI security scheme that handles OAuth2 authentication
    with Keycloak using the Authorization Code flow.

    Args:
        keycloak: Keycloak configuration settings

    Returns:
        OAuth2AuthorizationCodeBearer instance configured for Keycloak

    Example:
        ```python
        from dishka import FromDishka
        from fastapi import Depends

        oauth2_scheme = create_oauth2_scheme(settings.keycloak)
        if oauth2_scheme:
            @app.get("/protected")
            async def protected_route(token: str = Depends(oauth2_scheme)):
                # Token is automatically extracted from Authorization header
                return {"token": token}
        ```
    """

    return OAuth2AuthorizationCodeBearer(
        authorizationUrl=keycloak.get_authorization_url(),
        tokenUrl=keycloak.get_token_url(),
        scopes=keycloak.get_scopes_dict(),
        auto_error=True,
    )


def get_oauth2_urls(keycloak: KeycloakSettings) -> dict[str, str]:
    """
    Get all OAuth2 endpoint URLs for Keycloak.

    Useful for debugging or displaying configuration information.

    Args:
        keycloak: Keycloak configuration settings

    Returns:
        Dictionary with all OAuth2 endpoint URLs

    Example:
        ```python
        urls = get_oauth2_urls(settings.keycloak)
        print(urls["authorization_url"])
        # Output: http://localhost:8080/realms/eq-prepaid/protocol/openid-connect/auth
        ```
    """

    return {
        "realm_url": keycloak.get_realm_url(),
        "authorization_url": keycloak.get_authorization_url(),
        "token_url": keycloak.get_token_url(),
        "userinfo_url": keycloak.get_userinfo_url(),
        "jwks_url": keycloak.get_jwks_url(),
        "logout_url": keycloak.get_logout_url(),
    }
