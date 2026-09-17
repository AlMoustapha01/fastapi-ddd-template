"""Dishka provider for OAuth2 security."""

from dishka import Provider, Scope, provide
from fastapi.security import OAuth2AuthorizationCodeBearer

from core.config.keycloak import KeycloakSettings
from core.security.oauth2 import create_oauth2_scheme


class OAuth2Provider(Provider):
    """Provider for OAuth2 security dependencies."""

    scope = Scope.APP

    @provide
    def oauth2_scheme(
        self, keycloak: KeycloakSettings
    ) -> OAuth2AuthorizationCodeBearer | None:
        """
        Provide OAuth2 authorization code bearer scheme.

        This can be injected into route handlers to protect endpoints.
        Returns None if OAuth2 is not configured.

        Example:
            ```python
            from dishka.integrations.fastapi import inject
            from fastapi import APIRouter
            from fastapi.security import OAuth2AuthorizationCodeBearer

            router = APIRouter()

            @router.get("/protected")
            @inject
            async def protected_route(
                oauth2: FromDishka[OAuth2AuthorizationCodeBearer | None],
                token: str = Depends(oauth2) if oauth2 else None
            ):
                if not oauth2:
                    raise HTTPException(401, "OAuth2 not configured")
                return {"token": token}
            ```
        """
        return create_oauth2_scheme(keycloak)
