"""Database provider for Dishka dependency injection."""

import logging
from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config.database.config import PostgresSettings, SqlaEngineSettings

log = logging.getLogger(__name__)


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_async_engine(
        self,
        postgres: PostgresSettings,
        sqla_engine: SqlaEngineSettings,
    ) -> AsyncIterator[AsyncEngine]:
        async_engine = create_async_engine(
            url=postgres.dsn,
            echo=sqla_engine.echo,
            echo_pool=sqla_engine.echo_pool,
            pool_size=sqla_engine.pool_size,
            max_overflow=sqla_engine.max_overflow,
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True,
        )
        log.debug("Async engine created with DSN: %s", postgres.dsn)
        yield async_engine
        log.debug("Disposing async engine...")
        await async_engine.dispose()
        log.debug("Engine is disposed.")

    @provide(scope=Scope.APP)
    def provide_async_session_factory(
        self,
        engine: AsyncEngine,
    ) -> async_sessionmaker[AsyncSession]:
        async_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,
            expire_on_commit=False,
        )
        log.debug("Async session maker initialized.")
        return async_session_factory

    @provide(scope=Scope.REQUEST)
    async def provide_session(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        """Provide async session for request scope."""
        async with session_factory() as session:
            yield session
        log.debug("Session closed.")
