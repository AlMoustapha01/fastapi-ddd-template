"""Import every ORM model so that `Base.metadata` describes the whole schema."""

from core.infrastructure.db.base import Base

__all__ = ["Base"]
