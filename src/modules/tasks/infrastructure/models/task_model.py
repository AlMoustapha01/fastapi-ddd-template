"""ORM model of the `tasks` table."""

from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.infrastructure.db.base import Base
from core.infrastructure.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from modules.tasks.domain.enums import TaskStatus

STATUS_VALUES = ", ".join(f"'{status.value}'" for status in TaskStatus)


class TaskModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """`project_id` has no foreign key: `projects` belongs to another module."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(f"status IN ({STATUS_VALUES})", name="status"),
        Index("ix_tasks_project_id_status", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
