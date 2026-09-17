"""Project name."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MIN_LENGTH: Final[int] = 1
MAX_LENGTH: Final[int] = 100


@dataclass(frozen=True, slots=True, repr=False)
class ProjectName(ValueObject):
    """Unique human-readable name; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise DomainValidationError(
                f"Project name must be {MIN_LENGTH} to {MAX_LENGTH} characters long.",
                code="invalid_project_name",
                details={"min_length": MIN_LENGTH, "max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
