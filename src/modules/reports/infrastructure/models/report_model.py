"""Report SQLAlchemy model."""

from typing import Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import text

from core.lib.db.model_base import Base, UUIDTimestampMixin
from modules.rules.domain.enums import BalanceType, ProfileType


class ReportModel(Base, UUIDTimestampMixin):
    """SQLAlchemy model for Report entity."""

    __tablename__ = "report"

    title: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, doc="Report title"
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=False, default="", doc="Report description"
    )

    profile_type: Mapped[ProfileType] = mapped_column(
        Enum(ProfileType),
        nullable=False,
        doc="Type of profile this report applies to",
    )

    balance_type: Mapped[BalanceType] = mapped_column(
        Enum(BalanceType),
        nullable=False,
        doc="Type of balance this report affects",
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB(none_as_null=True),
        nullable=False,
        doc="Report configuration parameters in JSON format",
        server_default=text("'{}'"),
    )

    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        doc="User who created this report",
    )
