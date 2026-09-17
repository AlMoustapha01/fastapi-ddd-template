"""Base classes for domain events and aggregate roots."""

from abc import ABC
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar
from uuid import UUID

import uuid_utils.compat as uuid_utils

AggregateIdType = TypeVar("AggregateIdType")


@dataclass(frozen=True, kw_only=True)
class DomainEvent(ABC):  # noqa: B024
    """
    Base class for all domain events.

    Domain events represent something meaningful that happened in the domain.
    They are immutable and capture the state at the time of occurrence.
    """

    event_id: UUID = field(default_factory=uuid_utils.uuid7)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        """Return the name of the event (class name by default)."""
        return self.__class__.__name__
