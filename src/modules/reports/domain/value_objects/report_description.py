"""ReportDescription value object."""

from dataclasses import dataclass

from core.lib.base.value_object import ValueObject

MAX_DESCRIPTION_LENGTH = 1000


@dataclass(frozen=True, slots=True, repr=False)
class ReportDescription(ValueObject):
    """Value object representing a Report description."""

    value: str

    def __post_init__(self) -> None:
        """Validate description constraints."""
        if self.value and len(self.value) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Report description cannot exceed {MAX_DESCRIPTION_LENGTH} characters"
            )
