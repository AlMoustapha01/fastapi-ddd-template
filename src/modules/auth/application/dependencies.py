"""Authentication dependencies."""

import logging
from collections.abc import Callable
from contextvars import ContextVar
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import JWTDecoder

log = logging.getLogger(__name__)

# Context variable for current user
user_context: ContextVar[AuthUser | None] = ContextVar("user_context", default=None)

# HTTP Bearer security scheme
security = HTTPBearer()


@inject
def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    jwt_decoder: FromDishka[JWTDecoder],
) -> AuthUser:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization credentials
        jwt_decoder: JWT decoder (injected by Dishka)

    Returns:
        AuthUser

    Raises:
        HTTPException: 401 if token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        user = jwt_decoder.extract_user(token)
        user_context.set(user)
        log.debug("User authenticated: %s", user.username)
        return user
    except JWTError as err:
        log.warning("Authentication failed: %s", err)
        raise credentials_exception from err


def get_user_from_context() -> AuthUser | None:
    """Get current user from context variable."""
    return user_context.get()


def require_roles(required_roles: list[str]) -> Callable[[AuthUser], AuthUser]:
    """
    Dependency factory for role-based access control.

    User needs at least one of the required roles.

    Args:
        required_roles: List of role names

    Returns:
        Dependency function
    """

    def check_roles(user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
        if not user.has_any_role(required_roles):
            log.warning(
                "User %s denied. Required: %s, Has: %s",
                user.username,
                required_roles,
                user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Required roles: " + ", ".join(required_roles),
            )
        return user

    return check_roles


def require_all_roles(required_roles: list[str]) -> Callable[[AuthUser], AuthUser]:
    """
    Dependency factory for strict role-based access control.

    User needs all of the required roles.

    Args:
        required_roles: List of role names

    Returns:
        Dependency function
    """

    def check_all_roles(
        user: Annotated[AuthUser, Depends(get_current_user)],
    ) -> AuthUser:
        if not user.has_all_roles(required_roles):
            log.warning(
                "User %s denied. Required all: %s, Has: %s",
                user.username,
                required_roles,
                user.roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required all roles: {', '.join(required_roles)}",
            )
        return user

    return check_all_roles
