"""Report domain exceptions."""

from typing import Any

from core.lib.base.domain_error import DomainError


class ReportError(DomainError):
    """Base error for Report domain operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "REPORT_ERROR",
            details=details or {},
            cause=cause,
        )


class ReportAlreadyExistsError(ReportError):
    """Raised when a report with the same title already exists."""

    def __init__(
        self,
        title: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Report with title '{title}' already exists",
            code="REPORT_ALREADY_EXISTS",
            details={"title": title},
            cause=cause,
        )


class ReportNotFoundError(ReportError):
    """Raised when a report is not found."""

    def __init__(
        self,
        report_id: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Report with id '{report_id}' not found",
            code="REPORT_NOT_FOUND",
            details={"report_id": report_id},
            cause=cause,
        )


class ReportValidationError(ReportError):
    """Raised when report validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="REPORT_VALIDATION_ERROR",
            details=details,
            cause=cause,
        )
