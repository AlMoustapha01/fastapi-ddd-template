from typing import Protocol

from core.lib.db.repository import BaseRepositoryPort
from modules.rules.domain.entities.section import Section


class SectionRepositoryPort(BaseRepositoryPort[Section], Protocol):
    """Port interface for Section persistence."""

    async def find_one_by_slug(self, slug: str) -> Section | None:
        """Find an entity by its slug."""
