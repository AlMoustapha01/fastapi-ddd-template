"""Business error hierarchy. The category decides the HTTP status."""

from typing import Any, ClassVar


class DomainError(Exception):
    """Base class of every error raised by the domain and application layers."""

    default_code: ClassVar[str] = "domain_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details: dict[str, Any] = details or {}


class NotFoundError(DomainError):
    default_code = "not_found"


class ConflictError(DomainError):
    default_code = "conflict"


class BusinessRuleViolationError(DomainError):
    default_code = "business_rule_violation"


class DomainValidationError(DomainError):
    default_code = "validation_error"
