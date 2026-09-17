"""Request-scoped registry of the aggregates handled by repositories."""

from typing import Any

from core.domain.aggregate_root import AggregateRoot
from core.domain.events import DomainEvent


class AggregateTracker:
    """Remember the aggregates touched during a request to publish their events."""

    def __init__(self) -> None:
        self._aggregates: dict[int, AggregateRoot[Any, Any]] = {}

    def track(self, aggregate: AggregateRoot[Any, Any]) -> None:
        self._aggregates.setdefault(id(aggregate), aggregate)

    def pull_events(self) -> list[DomainEvent]:
        """Return the pending events of every tracked aggregate, in tracking order."""
        return [
            event
            for aggregate in self._aggregates.values()
            for event in aggregate.pull_events()
        ]
