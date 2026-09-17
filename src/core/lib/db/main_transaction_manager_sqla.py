import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.base.domain_error import DomainError

from .constants import DB_COMMIT_DONE
from .transaction_manager import TransactionManager

log = logging.getLogger(__name__)


class TransactionError(DomainError):
    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or "TRANSACTION_ERROR",
            details=details or {},
            cause=cause,
        )


class SqlaMainTransactionManager(TransactionManager):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        """:raises TransactionError:"""
        try:
            await self._session.commit()
            log.debug("%s Main session.", DB_COMMIT_DONE)

        except SQLAlchemyError as err:
            raise TransactionError(
                message="Failed to commit transaction",
                code="TRANSACTION_COMMIT_ERROR",
                cause=err,
            ) from err
