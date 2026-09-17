from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from core.lib.db.model_base import Base, UUIDTimestampMixin


class UserModel(Base, UUIDTimestampMixin):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True, doc="User full name"
    )

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True, doc="User email address"
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        doc="Unique username for the user",
    )

    keycloak_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Keycloak user identifier",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=False, default=True, doc="User activity status"
    )
