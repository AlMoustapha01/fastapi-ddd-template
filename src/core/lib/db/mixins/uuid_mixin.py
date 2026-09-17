import uuid_utils.compat as uuid_utils
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDMixin:
    """Mixin for adding UUID primary key to models."""

    id: Mapped[uuid_utils.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_utils.uuid7, nullable=False
    )
