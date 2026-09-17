"""Base database model and utilities."""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from core.lib.db.mixins import TimestampMixin, UUIDMixin


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models."""


class UUIDTimestampMixin(UUIDMixin, TimestampMixin):
    """Mixin combining UUID primary key and timestamp fields."""
