from dataclasses import dataclass
from uuid import UUID

from core.lib.base.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class RuleId(ValueObject):
    value: UUID
