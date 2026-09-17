import re
from dataclasses import dataclass

from slugify import slugify

from core.lib.base.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class SlugValueObject(ValueObject):
    value: str

    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        """Validate slug format: lowercase letters, numbers, and hyphens only"""
        return bool(re.match(r"^[a-z0-9-]+$", slug))

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Slug cannot be empty")
        if not self._is_valid_slug(self.value):
            raise ValueError("Invalid slug format")

    @classmethod
    def from_text(cls, text: str) -> "SlugValueObject":
        """Generate a slug from a text"""
        if not text:
            raise ValueError("Text cannot be empty")

        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = slugify(text, separator="-")

        if not slug:
            raise ValueError("Cannot generate valid slug from provided text")

        return cls(slug)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SlugValueObject):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.value)
