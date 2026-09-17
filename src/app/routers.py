"""HTTP routing of the application."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from core.presentation.http.health import create_health_router
from modules.projects.presentation.http.router import create_projects_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(create_projects_router())
    return router


def create_root_router(*, docs_enabled: bool) -> APIRouter:
    router = APIRouter()

    if docs_enabled:

        @router.get("/", include_in_schema=False)
        async def redirect_to_docs() -> RedirectResponse:
            return RedirectResponse(url="/docs")

    router.include_router(create_health_router())
    router.include_router(create_api_v1_router())
    return router
