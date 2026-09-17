"""Minimal domain model used to test the core building blocks."""

from dataclasses import dataclass

from core.domain.aggregate_root import AggregateRoot
from core.domain.errors import DomainValidationError
from core.domain.events import DomainEvent
from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class SampleId(EntityId):
    """Identifier of `SampleAggregate`."""


@dataclass(slots=True)
class SampleProps:
    label: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleRenamed(DomainEvent):
    label: str


class SampleAggregate(AggregateRoot[SampleId, SampleProps]):
    def rename(self, label: str) -> None:
        self.props.label = label
        self.touch()
        self.record_event(SampleRenamed(label=label))

    def validate(self) -> None:
        if not self.props.label:
            raise DomainValidationError("Label is required.", code="invalid_label")


def make_sample(label: str = "first") -> SampleAggregate:
    return SampleAggregate(id_=SampleId.generate(), props=SampleProps(label=label))
