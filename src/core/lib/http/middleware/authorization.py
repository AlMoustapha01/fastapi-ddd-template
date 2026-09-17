"""Authentication middleware for FastAPI."""

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from core.config.keycloak import KeycloakSettings
from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import JWTDecoder
from modules.users.infrastructure.repositories import UserRepository

log = logging.getLogger(__name__)

# Public endpoints that don't require authentication
PUBLIC_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
}


class AuthorizationMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce authentication on all endpoints except public ones."""

    def __init__(
        self,
        app: ASGIApp,
        keycloak_settings: KeycloakSettings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        """
        Initialize authentication middleware.

        Args:
            app: FastAPI application
            keycloak_settings: Keycloak configuration settings
            session_factory: SQLAlchemy async session factory
        """
        super().__init__(app)
        self.jwt_decoder = JWTDecoder(keycloak_settings)
        self.session_factory = session_factory

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Process request and enforce authentication.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Validate authentication
        error_response = await self._validate_authentication(request)
        if error_response:
            return error_response

        # Continue to next middleware/handler
        return await call_next(request)

    async def _validate_authentication(self, request: Request) -> JSONResponse | None:
        """
        Validate authentication and store user in request state.

        Args:
            request: Incoming request

        Returns:
            JSONResponse if authentication fails, None otherwise
        """
        # Extract token from Authorization header (case-insensitive)
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            log.warning(
                "Missing or invalid Authorization header for %s", request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing or invalid Authorization header",
                    "error": "unauthorized",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ")[1]

        # Validate token and extract user
        try:
            auth_user: AuthUser = self.jwt_decoder.extract_user(token)

            # Get user from database and verify they're active
            async with self.session_factory() as session:
                user_repo = UserRepository(session)
                user = await user_repo.find_one_by_keycloak_id(auth_user.id)

                if user is None:
                    log.warning(
                        "User not found in database for keycloak_id: %s",
                        auth_user.id,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "User not found",
                            "error": "user_not_found",
                        },
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                if not user.props.is_active:
                    log.warning(
                        "Inactive user attempted to access %s: %s",
                        request.url.path,
                        user.props.username,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": "User account is inactive",
                            "error": "user_inactive",
                        },
                    )

            # Store auth user in request state for later use
            request.state.user = auth_user
            request.state.db_user = user
            log.debug("User authenticated via middleware: %s", auth_user.username)
            return None

        except JWTError as err:
            log.warning("JWT validation failed for %s: %s", request.url.path, err)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Could not validate credentials",
                    "error": "invalid_token",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as err:
            log.error("Authentication error for %s: %s", request.url.path, err)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal authentication error",
                    "error": "server_error",
                },
            )

    def _is_public_path(self, path: str) -> bool:
        """
        Check if path is public (doesn't require authentication).

        Args:
            path: Request path

        Returns:
            True if path is public
        """
        # Exact match or prefix match for docs
        return (
            path in PUBLIC_PATHS
            or path.startswith("/docs")
            or path.startswith("/redoc")
        )
