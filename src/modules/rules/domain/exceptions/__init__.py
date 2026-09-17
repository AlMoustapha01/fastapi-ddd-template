"""Domain exceptions for rules module."""

from .rule import (
    RuleAlreadyExistsError,
    RuleError,
    RuleInvalidStatusError,
    RuleNotFoundError,
    RuleValidationError,
)
from .section import (
    SectionAlreadyExistsError,
    SectionError,
    SectionNotFoundError,
    SectionValidationError,
)

__all__ = [
    "RuleAlreadyExistsError",
    "RuleError",
    "RuleInvalidStatusError",
    "RuleNotFoundError",
    "RuleValidationError",
    "SectionAlreadyExistsError",
    "SectionError",
    "SectionNotFoundError",
    "SectionValidationError",
]
