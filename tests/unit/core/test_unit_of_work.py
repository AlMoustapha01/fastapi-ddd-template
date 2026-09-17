"""SQLAlchemy unit of work, with the session replaced by a recording fake."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.errors import ConflictError
from core.domain.events import DomainEvent
from core.infrastructure.db.errors import map_integrity_error
from core.infrastructure.db.tracker import AggregateTracker
from core.infrastructure.db.unit_of_work import (
    MAX_EVENT_ROUNDS,
    EventDispatchLoopError,
    SqlaUnitOfWork,
)
from tests.unit.core.samples import make_sample


@dataclass(frozen=True)
class FakeDiagnostic:
    constraint_name: str | None


class FakeDriverError(Exception):
    """Mimics psycopg errors, which expose `sqlstate` and `diag.constraint_name`."""

    def __init__(self, sqlstate: str, constraint_name: str | None = None) -> None:
        super().__init__(f"driver error {sqlstate}")
        self.sqlstate = sqlstate
        self.diag = FakeDiagnostic(constraint_name)


def integrity_error(
    sqlstate: str, constraint_name: str | None = None
) -> IntegrityError:
    return IntegrityError("INSERT ...", {}, FakeDriverError(sqlstate, constraint_name))


class FakeSession:
    def __init__(self, commit_error: Exception | None = None) -> None:
        self.calls: list[str] = []
        self._commit_error = commit_error

    async def flush(self) -> None:
        self.calls.append("flush")

    async def commit(self) -> None:
        self.calls.append("commit")
        if self._commit_error is not None:
            raise self._commit_error

    async def rollback(self) -> None:
        self.calls.append("rollback")


class RecordingBus:
    def __init__(
        self,
        session: FakeSession,
        on_publish: Callable[[DomainEvent], None] | None = None,
    ) -> None:
        self.published: list[DomainEvent] = []
        self._session = session
        self._on_publish = on_publish

    async def publish(self, event: DomainEvent) -> None:
        self._session.calls.append(f"publish:{type(event).__name__}")
        self.published.append(event)
        if self._on_publish is not None:
            self._on_publish(event)


def make_uow(
    session: FakeSession, tracker: AggregateTracker, bus: RecordingBus
) -> SqlaUnitOfWork:
    return SqlaUnitOfWork(
        session=cast(AsyncSession, session), tracker=tracker, event_bus=bus
    )


async def test_commit_without_events_flushes_then_commits() -> None:
    session = FakeSession()

    await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert session.calls == ["flush", "commit"]


async def test_commit_publishes_recorded_events_before_committing() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("second")
    tracker.track(aggregate)

    await make_uow(session, tracker, RecordingBus(session)).commit()

    assert session.calls == ["flush", "publish:SampleRenamed", "flush", "commit"]


async def test_events_recorded_by_handlers_are_published_in_a_next_round() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    first, second = make_sample("a"), make_sample("b")
    first.rename("a2")
    tracker.track(first)
    tracker.track(second)

    def rename_second_once(_event: DomainEvent) -> None:
        if second.props.label == "b":
            second.rename("b2")

    bus = RecordingBus(session, on_publish=rename_second_once)
    await make_uow(session, tracker, bus).commit()

    assert session.calls == [
        "flush",
        "publish:SampleRenamed",
        "flush",
        "publish:SampleRenamed",
        "flush",
        "commit",
    ]


async def test_dispatch_that_never_converges_is_aborted_and_rolled_back() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("again")
    tracker.track(aggregate)
    bus = RecordingBus(session, on_publish=lambda _event: aggregate.rename("again"))

    with pytest.raises(EventDispatchLoopError):
        await make_uow(session, tracker, bus).commit()

    assert len(bus.published) == MAX_EVENT_ROUNDS
    assert "commit" not in session.calls
    assert session.calls[-1] == "rollback"


async def test_handler_failure_rolls_back_and_propagates() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("x")
    tracker.track(aggregate)

    def explode(_event: DomainEvent) -> None:
        raise RuntimeError("handler failed")

    bus = RecordingBus(session, on_publish=explode)
    with pytest.raises(RuntimeError, match="handler failed"):
        await make_uow(session, tracker, bus).commit()

    assert session.calls == ["flush", "publish:SampleRenamed", "rollback"]


async def test_unique_violation_becomes_a_conflict_error() -> None:
    session = FakeSession(commit_error=integrity_error("23505", "uq_samples_label"))

    with pytest.raises(ConflictError) as exc_info:
        await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert exc_info.value.code == "unique_violation"
    assert exc_info.value.details == {"constraint": "uq_samples_label"}
    assert session.calls == ["flush", "commit", "rollback"]


async def test_unknown_integrity_error_is_reraised_after_rollback() -> None:
    session = FakeSession(commit_error=integrity_error("23514"))

    with pytest.raises(IntegrityError):
        await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert session.calls[-1] == "rollback"


async def test_rollback_delegates_to_the_session() -> None:
    session = FakeSession()

    await make_uow(session, AggregateTracker(), RecordingBus(session)).rollback()

    assert session.calls == ["rollback"]


@pytest.mark.parametrize(
    ("sqlstate", "code"),
    [("23505", "unique_violation"), ("23503", "foreign_key_violation")],
)
def test_map_integrity_error_known_sqlstates(sqlstate: str, code: str) -> None:
    error = map_integrity_error(integrity_error(sqlstate, "some_constraint"))

    assert isinstance(error, ConflictError)
    assert error.code == code
    assert error.details == {"constraint": "some_constraint"}


def test_map_integrity_error_without_constraint_name() -> None:
    error = map_integrity_error(integrity_error("23505"))

    assert error is not None
    assert error.details == {}


def test_map_integrity_error_unknown_sqlstate() -> None:
    assert map_integrity_error(integrity_error("23514")) is None
