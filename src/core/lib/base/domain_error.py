from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(eq=False)
class DomainError(Exception):
    """
    Domain exception (DDD) to signal a business rule violation.
    - message: human-readable description of the problem
    - code: short identifier (e.g. "ROLE_EMPTY_NAME")
    - details: structured context (e.g. {"role_id": "...", "tenant_id": "..."})
    - cause: original exception (facilitates exception chaining)
    """

    message: str
    code: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    cause: Exception | None = None

    def __post_init__(self) -> None:
        # Initialise Exception with the message
        super().__init__(self.message)
        # Preserve exception chaining (raise ... from ...)
        if self.cause is not None:
            self.__cause__ = self.cause

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}" if self.code else self.message

    def __repr__(self) -> str:
        return (
            f"DomainError(code={self.code!r}, "
            f"message={self.message!r}, "
            f"details={self.details!r}, "
            f"cause={repr(self.cause) if self.cause else None})"
        )

    def with_details(self, **extra: Any) -> DomainError:
        """Return a copy of the error with merged extra details."""
        d = {**self.details, **extra}
        return DomainError(
            self.message,
            code=self.code,
            details=d,
            cause=self.cause,
        )

    @classmethod
    def from_cause(
        cls, message: str, cause: Exception, code: str | None = None
    ) -> DomainError:
        """Factory method to wrap another exception as the cause."""
        return cls(message=message, code=code, cause=cause)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the error for logging or API responses."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "cause": repr(self.cause) if self.cause else None,
        }
