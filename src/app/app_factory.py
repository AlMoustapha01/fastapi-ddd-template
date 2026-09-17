from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, Provider, make_async_container
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.provider_registry import get_providers
from app.root_router import create_root_router
from core.config.settings import Settings
from core.lib.http.middleware.authorization import AuthorizationMiddleware


def create_ioc_container(
    settings: Settings,
    *di_providers: Provider,
) -> AsyncContainer:
    return make_async_container(
        *get_providers(),
        *di_providers,
        context={Settings: settings},
    )


def create_web_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
    )
    app.include_router(create_root_router())

    origins = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add authentication middleware if settings are provided
    if settings is not None:
        # Create async engine and session factory for middleware
        async_engine = create_async_engine(
            url=settings.postgres.dsn,
            echo=settings.sqla.echo,
            echo_pool=settings.sqla.echo_pool,
            pool_size=settings.sqla.pool_size,
            max_overflow=settings.sqla.max_overflow,
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True,
        )

        session_factory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )

        app.add_middleware(
            AuthorizationMiddleware,
            keycloak_settings=settings.keycloak,
            session_factory=session_factory,
        )

    return app


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield None
    await app.state.dishka_container.close()
