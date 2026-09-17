"""SQLAlchemy model for Rule audit events."""

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PGUUID,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.lib.db.model_base import Base
from modules.rules.domain.enums import RuleEventType

if TYPE_CHECKING:
    from modules.rules.infrastructure.models.rule_model import RuleModel


class RuleAuditEventModel(Base):
    """
    SQLAlchemy model for the rule_audit_events table.

    Stores all domain events for audit purposes.
    """

    __tablename__ = "rule_audit_event"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, doc="Event ID"
    )

    # Foreign key to rule
    rule_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("rule.id", ondelete="CASCADE"),
        nullable=False,
        doc="Rule this event belongs to",
    )

    # Event metadata
    event_type: Mapped[RuleEventType] = mapped_column(
        Enum(RuleEventType),
        nullable=False,
        doc="Type of event that occurred",
    )

    # Who performed the action
    performed_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        doc="User who performed the action",
    )

    # When the event occurred
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When the event occurred",
    )

    # Optional reason/comment
    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="Optional reason or comment"
    )

    # Status transition fields (for status change events)
    previous_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="Previous status (for status change events)"
    )

    new_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="New status (for status change events)"
    )

    # Snapshot of changes (stores old/new values as JSON)
    changes: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB(none_as_null=True),
        nullable=True,
        doc="Snapshot of changes (old/new values)",
    )

    # Timestamp when record was created (may differ from occurred_at)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="When this record was created in the database",
    )

    # Relationships
    rule: Mapped["RuleModel"] = relationship(
        "RuleModel",
        back_populates="audit_events",
    )

    # Indexes
    __table_args__ = (
        Index("idx_rule_audit_events_rule_id", "rule_id"),
        Index("idx_rule_audit_events_performed_by", "performed_by_user_id"),
        Index("idx_rule_audit_events_event_type", "event_type"),
        Index("idx_rule_audit_events_occurred_at", "occurred_at"),
        Index(
            "idx_rule_audit_events_rule_occurred",
            "rule_id",
            "occurred_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RuleAuditEventModel("
            f"id={self.id}, "
            f"rule_id={self.rule_id}, "
            f"event_type={self.event_type}, "
            f"occurred_at={self.occurred_at}"
            f")>"
        )
