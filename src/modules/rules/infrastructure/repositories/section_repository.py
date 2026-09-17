"""Section repository implementation."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.db.repository import BaseRepository
from core.lib.db.repository.errors import EntityQueryError
from modules.rules.domain.entities.section import Section
from modules.rules.domain.ports import SectionRepositoryPort
from modules.rules.infrastructure.mappers import SectionMapper
from modules.rules.infrastructure.models.section_model import SectionModel


class SectionRepository(BaseRepository[Section, SectionModel], SectionRepositoryPort):
    """Repository implementation for Section entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            model=SectionModel,
            mapper=SectionMapper(),
        )

    async def find_one_by_slug(self, slug: str) -> Section | None:
        """Find a single entity by its slug."""
        try:
            stmt = select(self.model).where(self.model.slug == slug)
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by slug",
                cause=e,
                details={"slug": slug},
            ) from e
