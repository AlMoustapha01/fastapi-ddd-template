"""Unit of work contract."""

from typing import Protocol


class UnitOfWork(Protocol):
    """Atomic business transaction shared by every repository of a request."""

    async def commit(self) -> None:
        """
        Publish pending domain events, then persist every change atomically.

        :raises ConflictError: when a database constraint is violated.
        """
        ...

    async def rollback(self) -> None:
        """Discard every pending change."""
        ...
