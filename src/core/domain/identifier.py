"""UUID-based identity value object."""

from dataclasses import dataclass
from typing import Self
from uuid import UUID

import uuid_utils.compat as uuid_utils

from core.domain.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class EntityId(ValueObject):
    """Identity of an entity. Subclass it once per aggregate (e.g. `ProjectId`)."""

    value: UUID

    @classmethod
    def generate(cls) -> Self:
        return cls(uuid_utils.uuid7())
