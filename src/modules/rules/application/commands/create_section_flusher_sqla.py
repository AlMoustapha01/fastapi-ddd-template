import logging
from typing import Any

from psycopg.errors import UniqueViolation
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
from modules.rules.domain.exceptions import SectionAlreadyExistsError

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


class SqlaSectionFlusher(Flusher):
    """Flusher for Section operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _extract_value_from_detail(detail: str | None) -> str:
        """
        Extract the value from PostgreSQL detail message.

        Format: "Key (column)=(value) already exists."
        """
        if not detail:
            return "unknown"
        # Find content between )=( and ) already
        start = detail.find(")=(")
        if start == -1:
            return "unknown"
        start += 3  # Skip ")=("
        end = detail.find(")", start)
        if end == -1:
            return "unknown"
        return detail[start:end]

    async def flush(self) -> None:
        """
        Flush pending changes to the database.

        :raises SectionAlreadyExistsError: When section slug already exists
        :raises FlushError: For other database errors
        """
        try:
            await self._session.flush()
            log.debug("%s Section session.", DB_FLUSH_DONE)

        except IntegrityError as err:
            orig = err.orig
            if isinstance(orig, UniqueViolation):
                constraint = orig.diag.constraint_name
                if constraint == "ix_section_slug":
                    slug = self._extract_value_from_detail(orig.diag.message_detail)
                    raise SectionAlreadyExistsError(slug) from err

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
