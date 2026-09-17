"""Readiness against a real database and consistency of migrations with models."""

from http import HTTPStatus

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient


async def test_readiness_is_ok_when_the_database_is_reachable(
    client: AsyncClient,
) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures("migrated_database")
async def test_migrations_match_the_orm_models(alembic_config: Config) -> None:
    command.check(alembic_config)
