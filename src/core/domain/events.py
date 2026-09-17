"""Base class for domain events."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import uuid_utils.compat as uuid_utils


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Immutable record of something meaningful that happened in the domain."""

    event_id: UUID = field(default_factory=uuid_utils.uuid7)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
