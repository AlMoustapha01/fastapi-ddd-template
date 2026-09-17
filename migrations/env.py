"""Alembic environment: application settings and metadata of every ORM model."""

import logging

from alembic import context
from sqlalchemy import URL, create_engine, pool

from app.models import Base
from core.infrastructure.settings import Settings

config = context.config
target_metadata = Base.metadata

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-5.5s %(message)s")


def database_url() -> URL:
    """URL injected by the tests through `config.attributes`, else from settings."""
    url = config.attributes.get("database_url")
    if isinstance(url, URL):
        return url
    return Settings().database.url


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
