"""SQLAlchemy implementation of the unit of work."""

import logging
from typing import Final

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from core.application.event_bus import EventBus
from core.application.unit_of_work import UnitOfWork
from core.infrastructure.db.errors import (
    concurrent_modification_error,
    map_integrity_error,
)
from core.infrastructure.db.tracker import AggregateTracker

log = logging.getLogger(__name__)

MAX_EVENT_ROUNDS: Final[int] = 10


class EventDispatchLoopError(RuntimeError):
    """Handlers kept recording events after `MAX_EVENT_ROUNDS` dispatch rounds."""


class SqlaUnitOfWork(UnitOfWork):
    """
    Commit a business transaction atomically.

    Each dispatch round flushes pending changes, then publishes the events recorded
    by tracked aggregates. Handlers run in the same session and may record new
    events, published in the next round. The session is committed once no event is
    left; any failure rolls the whole transaction back. Optimistic locking failures
    (`StaleDataError`) and known integrity errors become `ConflictError`.
    """

    def __init__(
        self, session: AsyncSession, tracker: AggregateTracker, event_bus: EventBus
    ) -> None:
        self._session = session
        self._tracker = tracker
        self._event_bus = event_bus

    async def commit(self) -> None:
        try:
            await self._dispatch_events()
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            conflict = map_integrity_error(err)
            if conflict is None:
                raise
            raise conflict from err
        except StaleDataError as err:
            await self._session.rollback()
            raise concurrent_modification_error() from err
        except Exception:
            await self._session.rollback()
            raise
        log.debug("Transaction committed.")

    async def rollback(self) -> None:
        await self._session.rollback()

    async def _dispatch_events(self) -> None:
        for round_number in range(MAX_EVENT_ROUNDS + 1):
            await self._session.flush()
            events = self._tracker.pull_events()
            if not events:
                return
            if round_number == MAX_EVENT_ROUNDS:
                raise EventDispatchLoopError(
                    f"Events were still produced after {MAX_EVENT_ROUNDS} rounds."
                )
            for event in events:
                await self._event_bus.publish(event)
