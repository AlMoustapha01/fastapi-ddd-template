"""Base class for immutable value objects."""

from dataclasses import dataclass, fields
from typing import Any, Self


@dataclass(frozen=True, slots=True, repr=False)
class ValueObject:
    """
    Immutable object defined only by its attributes.

    Decorate subclasses with `@dataclass(frozen=True, slots=True, repr=False)` and
    validate invariants in `__post_init__` by raising `DomainValidationError`.
    Fields declared with `field(repr=False)` are hidden from `repr()`.
    """

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        if cls is ValueObject:
            raise TypeError("Base ValueObject cannot be instantiated directly.")
        if not fields(cls):
            raise TypeError(f"{cls.__name__} must have at least one field.")
        return object.__new__(cls)

    def __post_init__(self) -> None:
        """Validation hook for subclasses."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._repr_fields()})"

    def _repr_fields(self) -> str:
        visible = [item for item in fields(self) if item.repr]
        if not visible:
            return "<hidden>"
        if len(visible) == 1:
            return repr(getattr(self, visible[0].name))
        return ", ".join(
            f"{item.name}={getattr(self, item.name)!r}" for item in visible
        )
