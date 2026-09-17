"""Domain event publication contracts."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.domain.events import DomainEvent


class EventHandler[TEvent: DomainEvent](Protocol):
    """
    Reacts to one event type inside the unit of work that published it.

    Handlers share the publisher's transaction and must never commit.
    """

    async def handle(self, event: TEvent) -> None: ...


class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class EventHandlerRegistry:
    """Handler types to run for each event type, in order (exact type match)."""

    handlers: Mapping[type[DomainEvent], Sequence[type[EventHandler[Any]]]] = field(
        default_factory=dict
    )

    def handlers_for(self, event: DomainEvent) -> Sequence[type[EventHandler[Any]]]:
        return self.handlers.get(type(event), ())
