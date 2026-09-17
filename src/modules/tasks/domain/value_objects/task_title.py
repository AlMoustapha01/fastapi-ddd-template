"""Task title."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MIN_LENGTH: Final[int] = 1
MAX_LENGTH: Final[int] = 200


@dataclass(frozen=True, slots=True, repr=False)
class TaskTitle(ValueObject):
    """Short summary of the task; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise DomainValidationError(
                f"Task title must be {MIN_LENGTH} to {MAX_LENGTH} characters long.",
                code="invalid_task_title",
                details={"min_length": MIN_LENGTH, "max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
