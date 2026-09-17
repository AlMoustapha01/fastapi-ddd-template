import re
from dataclasses import dataclass

from core.lib.base.value_object import ValueObject

# ----------------------------------------------------
# Constants
# ----------------------------------------------------
MAX_EMAIL_LENGTH = 255

# Email validation regex pattern
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


@dataclass(frozen=True, slots=True, repr=False)
class Email(ValueObject):
    value: str

    def __post_init__(self) -> None:
        """Validate email on creation."""
        self._validate()

    def _validate(self) -> None:
        """Validate email format and length."""
        if not self.value or not self.value.strip():
            raise ValueError("Email cannot be empty")
        if len(self.value) > MAX_EMAIL_LENGTH:
            raise ValueError(f"Email cannot exceed {MAX_EMAIL_LENGTH} characters")
        if not EMAIL_PATTERN.match(self.value):
            raise ValueError("Invalid email format")

    @property
    def domain(self) -> str:
        """Extract domain from email address."""
        return self.value.split("@")[1] if "@" in self.value else ""

    @property
    def local_part(self) -> str:
        """Extract local part (before @) from email address."""
        return self.value.split("@")[0] if "@" in self.value else self.value
