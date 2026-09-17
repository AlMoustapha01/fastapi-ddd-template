"""ReportId value object."""

from dataclasses import dataclass
from uuid import UUID

from core.lib.base.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class ReportId(ValueObject):
    """Value object representing a Report ID."""

    value: UUID
