"""Registry mapping event types to handler types."""

from core.application.event_bus import EventHandlerRegistry
from core.domain.events import DomainEvent
from tests.unit.core.samples import SampleRenamed


class RecordingHandler:
    def __init__(self) -> None:
        self.received: list[DomainEvent] = []

    async def handle(self, event: SampleRenamed) -> None:
        self.received.append(event)


class OtherRecordingHandler(RecordingHandler):
    """A second handler type."""


def test_returns_registered_handlers_in_order() -> None:
    registry = EventHandlerRegistry(
        handlers={SampleRenamed: (RecordingHandler, OtherRecordingHandler)}
    )

    handlers = registry.handlers_for(SampleRenamed(label="x"))

    assert handlers == (RecordingHandler, OtherRecordingHandler)


def test_unregistered_event_has_no_handler() -> None:
    assert EventHandlerRegistry().handlers_for(SampleRenamed(label="x")) == ()
