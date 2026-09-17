"""Aggregate tracker used by repositories and the unit of work."""

from core.infrastructure.db.tracker import AggregateTracker
from tests.unit.core.samples import SampleRenamed, make_sample


def test_pull_events_collects_events_of_tracked_aggregates_once() -> None:
    first, second = make_sample("a"), make_sample("b")
    first.rename("a2")
    second.rename("b2")
    tracker = AggregateTracker()

    tracker.track(first)
    tracker.track(second)
    tracker.track(first)
    events = tracker.pull_events()

    labels = [event.label for event in events if isinstance(event, SampleRenamed)]
    assert labels == ["a2", "b2"]
    assert len(events) == 2
    assert tracker.pull_events() == []


def test_untracked_aggregates_are_ignored() -> None:
    aggregate = make_sample()
    aggregate.rename("changed")

    assert AggregateTracker().pull_events() == []
