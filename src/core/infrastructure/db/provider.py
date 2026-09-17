"""Database dependencies: one engine for the app, one session per request."""

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.application.unit_of_work import UnitOfWork
from core.infrastructure.db.tracker import AggregateTracker
from core.infrastructure.db.unit_of_work import SqlaUnitOfWork
from core.infrastructure.settings import DatabaseSettings

CONNECT_TIMEOUT_SECONDS = 5


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self, settings: DatabaseSettings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(
            settings.url,
            echo=settings.echo,
            echo_pool=settings.echo_pool,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_pre_ping=True,
            connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        )
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    tracker = provide(AggregateTracker, scope=Scope.REQUEST)
    unit_of_work = provide(SqlaUnitOfWork, scope=Scope.REQUEST, provides=UnitOfWork)
