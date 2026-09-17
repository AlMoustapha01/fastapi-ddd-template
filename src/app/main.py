"""FastAPI application factory (`uvicorn app.main:create_app --factory`)."""

from dishka import Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.lifespan import lifespan
from app.providers import get_providers
from app.routers import create_root_router
from core.infrastructure.logs import configure_logging
from core.infrastructure.settings import Settings
from core.presentation.http.errors import register_error_handlers


def create_app(settings: Settings | None = None, *providers: Provider) -> FastAPI:
    """
    Build the application.

    `providers` are registered after the default ones and therefore override them,
    which lets tests replace any dependency.
    """
    settings = settings or Settings()
    configure_logging(settings.log.level)
    docs_enabled = settings.app.docs_enabled

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )
    if settings.cors.allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_credentials=settings.cors.allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_error_handlers(app)
    app.include_router(create_root_router(docs_enabled=docs_enabled))

    container = make_async_container(
        *get_providers(), *providers, context={Settings: settings}
    )
    setup_dishka(container=container, app=app)
    return app
