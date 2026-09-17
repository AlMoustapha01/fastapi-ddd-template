"""In-process event bus resolving handlers from the Dishka request container."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
    provide,
    provide_all,
)

from core.application.event_bus import EventBus, EventHandlerRegistry
from core.domain.events import DomainEvent
from core.infrastructure.events.in_process_bus import InProcessEventBus
from tests.unit.core.samples import SampleRenamed


@dataclass(frozen=True, slots=True, kw_only=True)
class UnhandledEvent(DomainEvent):
    """Event without any registered handler."""


class Journal:
    def __init__(self) -> None:
        self.entries: list[str] = []


class FirstHandler:
    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    async def handle(self, event: SampleRenamed) -> None:
        self._journal.entries.append(f"first:{event.label}")


class SecondHandler:
    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    async def handle(self, event: SampleRenamed) -> None:
        self._journal.entries.append(f"second:{event.label}")


class BusTestProvider(Provider):
    scope = Scope.REQUEST

    journal = provide(Journal)
    handlers = provide_all(FirstHandler, SecondHandler)
    event_bus = provide(InProcessEventBus, provides=EventBus)

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={SampleRenamed: (FirstHandler, SecondHandler)}
        )


@pytest.fixture
async def scope() -> AsyncIterator[AsyncContainer]:
    container = make_async_container(BusTestProvider())
    async with container() as request_container:
        yield request_container
    await container.close()


async def test_publish_awaits_registered_handlers_in_order(
    scope: AsyncContainer,
) -> None:
    bus = await scope.get(EventBus)

    await bus.publish(SampleRenamed(label="x"))

    journal = await scope.get(Journal)
    assert journal.entries == ["first:x", "second:x"]


async def test_publish_without_handlers_does_nothing(scope: AsyncContainer) -> None:
    bus = await scope.get(EventBus)

    await bus.publish(UnhandledEvent())

    journal = await scope.get(Journal)
    assert journal.entries == []
