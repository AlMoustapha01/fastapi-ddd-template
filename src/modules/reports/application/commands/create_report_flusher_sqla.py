"""SQLAlchemy flusher for Report operations."""

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
from modules.reports.domain.exceptions import ReportAlreadyExistsError

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


class SqlaReportFlusher(Flusher):
    """Flusher for Report operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def flush(self) -> None:
        """
        Flush pending changes to the database.

        :raises ReportAlreadyExistsError: When report title already exists
        :raises FlushError: For other database errors
        """
        try:
            await self._session.flush()
            log.debug("%s Report session.", DB_FLUSH_DONE)

        except IntegrityError as err:
            # Check for unique constraint on title
            err_str = str(err).lower()
            if "title" in err_str and ("unique" in err_str or "duplicate" in err_str):
                params: Mapping[str, Any] = cast(Mapping[str, Any], err.params)
                title = str(params.get("title", "unknown"))
                raise ReportAlreadyExistsError(title) from err

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
