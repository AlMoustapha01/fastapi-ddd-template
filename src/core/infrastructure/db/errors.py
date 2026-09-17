"""Translate database integrity errors into domain errors."""

from typing import Any, Final

from sqlalchemy.exc import IntegrityError

from core.domain.errors import ConflictError

UNIQUE_VIOLATION: Final[str] = "23505"
FOREIGN_KEY_VIOLATION: Final[str] = "23503"


def map_integrity_error(error: IntegrityError) -> ConflictError | None:
    """Return the domain error matching the driver SQLSTATE, or `None` if unknown."""
    sqlstate = getattr(error.orig, "sqlstate", None)
    diagnostic = getattr(error.orig, "diag", None)
    constraint = getattr(diagnostic, "constraint_name", None)
    details: dict[str, Any] = {"constraint": constraint} if constraint else {}
    if sqlstate == UNIQUE_VIOLATION:
        return ConflictError(
            "The resource already exists.",
            code="unique_violation",
            details=details,
        )
    if sqlstate == FOREIGN_KEY_VIOLATION:
        return ConflictError(
            "The resource is linked to another resource.",
            code="foreign_key_violation",
            details=details,
        )
    return None
