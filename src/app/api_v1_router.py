from fastapi import APIRouter, Depends

from modules.auth import create_auth_router, get_current_user
from modules.reports.presentation.http.router import create_reports_router
from modules.rules.presentation.http.router import create_rules_router
from modules.users.presentation.http.router import create_users_router

from .general.router import create_general_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/v1",
    )

    # Auth router (public endpoints: login, logout, refresh)
    router.include_router(create_auth_router())

    # Protected routers (require authentication)
    protected_routers: tuple[APIRouter, ...] = (
        create_rules_router(),
        create_reports_router(),
        create_users_router(),
    )

    for sub_router in protected_routers:
        # Add authentication dependency to all routes in the sub-router
        sub_router.dependencies.append(Depends(get_current_user))
        router.include_router(sub_router)

    # General router (health check, etc. - no auth required)
    router.include_router(create_general_router())

    return router
