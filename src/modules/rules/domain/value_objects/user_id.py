"""UserId value object for audit trail."""

from dataclasses import dataclass
from uuid import UUID

from core.lib.base.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class UserId(ValueObject):
    """Value object representing a User ID for audit purposes."""

    value: UUID
