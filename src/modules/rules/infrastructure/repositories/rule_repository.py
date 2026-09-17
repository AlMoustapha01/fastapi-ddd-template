"""Rule repository implementation."""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.db.repository import BaseRepository
from core.lib.db.repository.errors import EntityQueryError
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.ports import RuleRepositoryPort
from modules.rules.infrastructure.mappers import RuleMapper
from modules.rules.infrastructure.models.rule_model import RuleModel


class RuleRepository(BaseRepository[Rule, RuleModel], RuleRepositoryPort):
    """Repository implementation for Rule entity."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(
            session=session,
            model=RuleModel,
            mapper=RuleMapper(),
        )

    async def find_one_by_slug(self, slug: str) -> Rule | None:
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
