"""ORM model of the `projects` table."""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.infrastructure.db.base import Base
from core.infrastructure.db.mixins import (
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    VersionMixin,
)
from modules.projects.domain.enums import ProjectStatus

STATUS_VALUES = ", ".join(f"'{status.value}'" for status in ProjectStatus)


class ProjectModel(UUIDPrimaryKeyMixin, VersionMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint(f"status IN ({STATUS_VALUES})", name="status"),)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
