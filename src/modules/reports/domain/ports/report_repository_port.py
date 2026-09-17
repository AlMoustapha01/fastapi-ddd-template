"""Report repository port."""

from typing import Protocol

from core.lib.db.repository import BaseRepositoryPort
from modules.reports.domain.entities.report import Report


class ReportRepositoryPort(BaseRepositoryPort[Report], Protocol):
    """Port interface for Report persistence."""

    async def find_one_by_title(self, title: str) -> Report | None:
        """Find a report by its title."""
