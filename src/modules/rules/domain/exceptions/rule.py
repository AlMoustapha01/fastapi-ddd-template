"""Rule domain exceptions."""

from typing import Any

from core.lib.base.domain_error import DomainError


class RuleError(DomainError):
    """Base error for Rule domain operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "RULE_ERROR",
            details=details or {},
            cause=cause,
        )


class RuleAlreadyExistsError(RuleError):
    """Raised when a rule with the same slug already exists."""

    def __init__(
        self,
        slug: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Rule with slug '{slug}' already exists",
            code="RULE_ALREADY_EXISTS",
            details={"slug": slug},
            cause=cause,
        )


class RuleNotFoundError(RuleError):
    """Raised when a rule is not found."""

    def __init__(
        self,
        rule_id: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Rule with id '{rule_id}' not found",
            code="RULE_NOT_FOUND",
            details={"rule_id": rule_id},
            cause=cause,
        )


class RuleValidationError(RuleError):
    """Raised when rule validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="RULE_VALIDATION_ERROR",
            details=details,
            cause=cause,
        )


class RuleInvalidStatusError(RuleError):
    """Raised when an operation is attempted on a rule with an invalid status."""

    def __init__(
        self,
        rule_id: str,
        current_status: str,
        allowed_statuses: list[str],
        operation: str,
        cause: Exception | None = None,
    ) -> None:
        allowed = ", ".join(allowed_statuses)
        super().__init__(
            message=f"Cannot {operation} rule in status {current_status}. "
            f"Only rules in status [{allowed}] can be {operation}d.",
            code="RULE_INVALID_STATUS",
            details={
                "rule_id": rule_id,
                "current_status": current_status,
                "allowed_statuses": allowed_statuses,
                "operation": operation,
            },
            cause=cause,
        )
