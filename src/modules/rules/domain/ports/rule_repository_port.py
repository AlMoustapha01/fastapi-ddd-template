from typing import Protocol

from core.lib.db.repository import BaseRepositoryPort
from modules.rules.domain.entities.rule import Rule


class RuleRepositoryPort(BaseRepositoryPort[Rule], Protocol):
    """Port interface for Rule persistence."""

    async def find_one_by_slug(self, slug: str) -> Rule | None:
        """Find an entity by its slug."""
