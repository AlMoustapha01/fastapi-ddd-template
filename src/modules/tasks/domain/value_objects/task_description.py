"""Task description."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MAX_LENGTH: Final[int] = 5000


@dataclass(frozen=True, slots=True, repr=False)
class TaskDescription(ValueObject):
    """Free text, possibly empty; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > MAX_LENGTH:
            raise DomainValidationError(
                f"Task description cannot exceed {MAX_LENGTH} characters.",
                code="invalid_task_description",
                details={"max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
