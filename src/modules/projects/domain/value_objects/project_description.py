"""Project description."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MAX_LENGTH: Final[int] = 2000


@dataclass(frozen=True, slots=True, repr=False)
class ProjectDescription(ValueObject):
    """Free text, possibly empty; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > MAX_LENGTH:
            raise DomainValidationError(
                f"Project description cannot exceed {MAX_LENGTH} characters.",
                code="invalid_project_description",
                details={"max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
