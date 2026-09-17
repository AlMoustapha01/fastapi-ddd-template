import logging
from collections.abc import Mapping
from typing import Any, cast

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.base.domain_error import DomainError
from core.lib.db.constants import (
    DB_CONSTRAINT_VIOLATION,
    DB_FLUSH_DONE,
    DB_FLUSH_FAILED,
    DB_QUERY_FAILED,
)
from core.lib.db.flusher import Flusher
from modules.users.domain.exceptions import UserAlreadyExistsError

log = logging.getLogger(__name__)


class FlushError(DomainError):
    """Error during flush operation."""

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "FLUSH_ERROR",
            details=details or {},
            cause=cause,
        )


class SqlaUserFlusher(Flusher):
    """Flusher for User operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def flush(self) -> None:
        """
        Flush pending changes to the database.

        :raises UserAlreadyExistsError:
        When user email/username/keycloak_id already exists
        :raises FlushError: For other database errors
        """
        try:
            await self._session.flush()
            log.debug("%s User session.", DB_FLUSH_DONE)

        except IntegrityError as err:
            # Check for unique constraint violations
            err_str = str(err).lower()
            params: Mapping[str, Any] = cast(Mapping[str, Any], err.params)

            if "email" in err_str and ("unique" in err_str or "duplicate" in err_str):
                email = str(params.get("email", "unknown"))
                raise UserAlreadyExistsError(
                    f"User with email {email} already exists"
                ) from err

            if "username" in err_str and (
                "unique" in err_str or "duplicate" in err_str
            ):
                username = str(params.get("username", "unknown"))
                raise UserAlreadyExistsError(
                    f"User with username {username} already exists"
                ) from err

            if "keycloak_id" in err_str and (
                "unique" in err_str or "duplicate" in err_str
            ):
                keycloak_id = str(params.get("keycloak_id", "unknown"))
                raise UserAlreadyExistsError(
                    f"User with keycloak_id {keycloak_id} already exists"
                ) from err

            raise FlushError(
                message=DB_CONSTRAINT_VIOLATION,
                code="FLUSH_CONSTRAINT_VIOLATION",
                cause=err,
            ) from err

        except SQLAlchemyError as err:
            raise FlushError(
                message=f"{DB_QUERY_FAILED} {DB_FLUSH_FAILED}",
                code="FLUSH_QUERY_FAILED",
                cause=err,
            ) from err
