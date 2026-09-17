"""Report repository implementation."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.db.repository import BaseRepository
from core.lib.db.repository.errors import EntityQueryError
from modules.reports.domain.entities.report import Report
from modules.reports.domain.ports import ReportRepositoryPort
from modules.reports.infrastructure.mappers import ReportMapper
from modules.reports.infrastructure.models.report_model import ReportModel


class ReportRepository(BaseRepository[Report, ReportModel], ReportRepositoryPort):
    """Repository implementation for Report entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            model=ReportModel,
            mapper=ReportMapper(),
        )

    async def find_one_by_title(self, title: str) -> Report | None:
        """Find a single report by its title."""
        try:
            stmt = select(self.model).where(self.model.title == title)
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by title",
                cause=e,
                details={"title": title},
            ) from e
