"""Repository-specific domain errors."""

from typing import Any

from core.lib.base.domain_error import DomainError


class RepositoryError(DomainError):
    """Base error for repository operations."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "REPOSITORY_ERROR",
            details=details or {},
            cause=cause,
        )


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found in the repository."""

    def __init__(
        self,
        entity_type: str,
        entity_id: Any,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"{entity_type} with id '{entity_id}' not found",
            code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": str(entity_id)},
            cause=cause,
        )


class EntityAddError(RepositoryError):
    """Raised when adding an entity fails."""

    def __init__(
        self,
        entity_type: str,
        cause: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Failed to add {entity_type}",
            code="ENTITY_ADD_ERROR",
            details={"entity_type": entity_type, **(details or {})},
            cause=cause,
        )


class EntitySaveError(RepositoryError):
    """Raised when saving an entity fails."""

    def __init__(
        self,
        entity_type: str,
        cause: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Failed to save {entity_type}",
            code="ENTITY_SAVE_ERROR",
            details={"entity_type": entity_type, **(details or {})},
            cause=cause,
        )


class EntityDeleteError(RepositoryError):
    """Raised when deleting an entity fails."""

    def __init__(
        self,
        entity_type: str,
        cause: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Failed to delete {entity_type}",
            code="ENTITY_DELETE_ERROR",
            details={"entity_type": entity_type, **(details or {})},
            cause=cause,
        )


class EntityQueryError(RepositoryError):
    """Raised when querying entities fails."""

    def __init__(
        self,
        entity_type: str,
        operation: str,
        cause: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=f"Failed to {operation} {entity_type}",
            code="ENTITY_QUERY_ERROR",
            details={
                "entity_type": entity_type,
                "operation": operation,
                **(details or {}),
            },
            cause=cause,
        )
