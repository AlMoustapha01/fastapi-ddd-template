"""Section domain exceptions."""

from typing import Any

from core.lib.base.domain_error import DomainError


class SectionError(DomainError):
    """Base error for Section domain operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "SECTION_ERROR",
            details=details or {},
            cause=cause,
        )


class SectionAlreadyExistsError(SectionError):
    """Raised when a section with the same slug already exists."""

    def __init__(
        self,
        slug: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Section with slug '{slug}' already exists",
            code="SECTION_ALREADY_EXISTS",
            details={"slug": slug},
            cause=cause,
        )


class SectionNotFoundError(SectionError):
    """Raised when a section is not found."""

    def __init__(
        self,
        section_id: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Section with id '{section_id}' not found",
            code="SECTION_NOT_FOUND",
            details={"section_id": section_id},
            cause=cause,
        )


class SectionValidationError(SectionError):
    """Raised when section validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="SECTION_VALIDATION_ERROR",
            details=details,
            cause=cause,
        )
