"""Aggregate root: consistency boundary that records domain events."""

from datetime import datetime

from core.domain.entity import Entity
from core.domain.events import DomainEvent
from core.domain.identifier import EntityId


class AggregateRoot[TId: EntityId, TProps](Entity[TId, TProps]):
    """Entity whose recorded events are published when its unit of work commits."""

    def __init__(
        self,
        *,
        id_: TId,
        props: TProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        self._events: list[DomainEvent] = []
        super().__init__(
            id_=id_, props=props, created_at_=created_at_, updated_at_=updated_at_
        )

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return the recorded events and forget them."""
        events, self._events = self._events, []
        return events
