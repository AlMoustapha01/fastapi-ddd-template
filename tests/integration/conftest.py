"""PostgreSQL-backed fixtures. Requires Docker."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.main import create_app
from core.infrastructure.settings import (
    AppSettings,
    DatabaseSettings,
    Environment,
    Settings,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSTGRES_IMAGE = "postgres:17-alpine"
LIST_TABLES = text(
    "SELECT tablename FROM pg_tables "
    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
)


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as container:
        yield container


@pytest.fixture(scope="session")
def database_settings(postgres: PostgresContainer) -> DatabaseSettings:
    return DatabaseSettings(
        host=postgres.get_container_host_ip(),
        port=int(postgres.get_exposed_port(5432)),
        user=postgres.username,
        password=SecretStr(postgres.password),
        name=postgres.dbname,
    )


@pytest.fixture(scope="session")
def alembic_config(database_settings: DatabaseSettings) -> Config:
    config = Config(toml_file=PROJECT_ROOT / "pyproject.toml")
    config.attributes["database_url"] = database_settings.url
    return config


@pytest.fixture(scope="session")
def migrated_database(
    database_settings: DatabaseSettings, alembic_config: Config
) -> DatabaseSettings:
    command.upgrade(alembic_config, "head")
    return database_settings


@pytest.fixture
def settings(migrated_database: DatabaseSettings) -> Settings:
    return Settings(
        app=AppSettings(environment=Environment.TEST),
        database=migrated_database,
        _env_file=None,
    )


@pytest.fixture
async def engine(migrated_database: DatabaseSettings) -> AsyncIterator[AsyncEngine]:
    async_engine = create_async_engine(migrated_database.url)
    yield async_engine
    await async_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(engine: AsyncEngine) -> None:
    """Empty every application table before each test."""
    async with engine.begin() as connection:
        tables: list[str] = list((await connection.execute(LIST_TABLES)).scalars())
        if tables:
            quoted = ", ".join(f'"{name}"' for name in tables)
            await connection.execute(
                text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE")
            )


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    yield application
    await application.state.dishka_container.close()


@pytest.fixture
def container(app: FastAPI) -> AsyncContainer:
    """Application-scoped Dishka container; `async with container() as scope:`."""
    return cast(AsyncContainer, app.state.dishka_container)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
