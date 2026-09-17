"""Main router for users module."""

from fastapi import APIRouter

from .controllers import (
    create_create_user_router,
    create_delete_user_router,
    create_export_users_router,
    create_get_user_by_id_router,
    create_get_users_router,
    create_invite_user_router,
    create_make_active_user_router,
    create_make_inactive_user_router,
    create_update_user_router,
)


def create_users_router() -> APIRouter:
    """
    Create the main router for users module.

    Returns:
        APIRouter with all users endpoints
    """
    router = APIRouter(prefix="/users", tags=["Users"])

    # User endpoints
    router.include_router(create_get_users_router())
    router.include_router(create_export_users_router())
    router.include_router(create_get_user_by_id_router())
    router.include_router(create_create_user_router())
    router.include_router(create_invite_user_router())
    router.include_router(create_update_user_router())
    router.include_router(create_make_active_user_router())
    router.include_router(create_make_inactive_user_router())
    router.include_router(create_delete_user_router())

    return router
