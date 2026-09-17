from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.lib.db.model_base import Base, UUIDTimestampMixin
from modules.rules.domain.enums import SectionStatus

if TYPE_CHECKING:
    from .rule_model import RuleModel


class SectionModel(Base, UUIDTimestampMixin):
    __tablename__ = "section"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, doc="Section name"
    )

    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, doc="Section slug"
    )

    description: Mapped[str] = mapped_column(
        Text, nullable=True, doc="Section description"
    )

    status: Mapped[SectionStatus] = mapped_column(
        Enum(SectionStatus),
        nullable=False,
        default=SectionStatus.ACTIVE,
        doc="Section status",
    )

    # Relationships
    rules: Mapped[list["RuleModel"]] = relationship(
        "RuleModel", back_populates="section"
    )

    created_by_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        doc="User who created this section",
    )
