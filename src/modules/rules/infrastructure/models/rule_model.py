from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ARRAY, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import text

from core.lib.db.model_base import Base, UUIDTimestampMixin
from modules.rules.domain.enums import BalanceType, ProfileType, RuleStatus

if TYPE_CHECKING:
    from .rule_audit_event_model import RuleAuditEventModel
    from .section_model import SectionModel


class RuleModel(Base, UUIDTimestampMixin):
    __tablename__ = "rule"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, doc="Rule name"
    )

    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, doc="Rule slug"
    )

    profile_type: Mapped[ProfileType] = mapped_column(
        Enum(ProfileType),
        nullable=False,
        doc="Type of profile this rule applies to",
    )

    balance_type: Mapped[BalanceType] = mapped_column(
        Enum(BalanceType),
        nullable=False,
        doc="Type of balance this rule affects",
    )

    section_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("section.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key to the section table",
    )

    section: Mapped["SectionModel"] = relationship(
        "SectionModel", back_populates="rules"
    )

    database_table_name: Mapped[list[str]] = mapped_column(
        ARRAY(String(255)),
        nullable=False,
        doc="List of database tables this rule applies to",
        server_default=text("'{}'"),
    )

    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB(none_as_null=True),
        nullable=False,
        doc="Rule configuration parameters in JSON format",
        server_default=text("'{}'"),
    )

    status: Mapped[RuleStatus] = mapped_column(
        Enum(RuleStatus),
        nullable=False,
        default=RuleStatus.DRAFT,
        doc="Rule status",
    )

    # Audit fields (denormalized for quick access)
    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        doc="User who created this rule",
    )

    last_modified_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=True,
        doc="User who last modified this rule",
    )

    # Relationships
    audit_events: Mapped[list["RuleAuditEventModel"]] = relationship(
        "RuleAuditEventModel",
        back_populates="rule",
        cascade="all, delete-orphan",
        order_by="desc(RuleAuditEventModel.occurred_at)",
    )
