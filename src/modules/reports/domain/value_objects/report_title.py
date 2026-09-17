"""ReportTitle value object."""

from dataclasses import dataclass

from core.lib.base.value_object import ValueObject

MAX_TITLE_LENGTH = 255
MIN_TITLE_LENGTH = 1


@dataclass(frozen=True, slots=True, repr=False)
class ReportTitle(ValueObject):
    """Value object representing a Report title."""

    value: str

    def __post_init__(self) -> None:
        """Validate title constraints."""
        if not self.value or not self.value.strip():
            raise ValueError("Report title cannot be empty")
        if len(self.value) < MIN_TITLE_LENGTH:
            raise ValueError(
                f"Report title must be at least {MIN_TITLE_LENGTH} characters"
            )
        if len(self.value) > MAX_TITLE_LENGTH:
            raise ValueError(
                f"Report title cannot exceed {MAX_TITLE_LENGTH} characters"
            )
