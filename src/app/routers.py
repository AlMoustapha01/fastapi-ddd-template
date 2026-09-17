"""HTTP routing of the application."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from core.presentation.http.health import create_health_router


def create_api_v1_router() -> APIRouter:
    return APIRouter(prefix="/api/v1")


def create_root_router(*, docs_enabled: bool) -> APIRouter:
    router = APIRouter()

    if docs_enabled:

        @router.get("/", include_in_schema=False)
        async def redirect_to_docs() -> RedirectResponse:
            return RedirectResponse(url="/docs")

    router.include_router(create_health_router())
    router.include_router(create_api_v1_router())
    return router
