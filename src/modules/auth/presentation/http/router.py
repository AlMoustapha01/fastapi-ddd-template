"""Main auth router."""

from fastapi import APIRouter

from .controllers import (
    create_groups_router,
    create_login_history_router,
    create_login_router,
    create_logout_router,
    create_me_router,
    create_permissions_router,
    create_refresh_token_router,
    create_users_router,
)


def create_auth_router() -> APIRouter:
    """Create main auth router."""
    router = APIRouter(prefix="/auth", tags=["Authentication"])

    # Public endpoints (no authentication required)
    router.include_router(create_login_router())
    router.include_router(create_logout_router())
    router.include_router(create_refresh_token_router())

    # Protected endpoints (authentication required)
    router.include_router(create_me_router())
    router.include_router(create_permissions_router())
    router.include_router(create_users_router())
    router.include_router(create_groups_router())
    router.include_router(create_login_history_router())

    return router
