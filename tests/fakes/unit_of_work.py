"""Unit of work double."""

from core.application.unit_of_work import UnitOfWork


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
