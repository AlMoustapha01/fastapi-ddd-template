from dataclasses import dataclass
from datetime import datetime

import uuid_utils.compat as uuid_utils

from core.lib.base.entity import Entity
from modules.users.domain.value_objects import Email, UserId


@dataclass
class UserProps:
    name: str
    email: Email
    username: str
    keycloak_id: str
    is_active: bool = True


@dataclass
class CreateUserProps:
    name: str
    email: str
    username: str
    keycloak_id: str


class User(Entity[UserId, UserProps]):
    def __init__(
        self,
        *,
        id_: UserId,
        props: UserProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        super().__init__(
            id_=id_,
            props=props,
            created_at_=created_at_,
            updated_at_=updated_at_,
        )
        self.validate()

    @staticmethod
    def create(props: CreateUserProps) -> "User":
        """Factory method to create a new User with default values."""
        id_ = UserId(uuid_utils.uuid7())

        full_props = UserProps(
            name=props.name,
            email=Email(props.email),
            username=props.username,
            keycloak_id=props.keycloak_id,
            is_active=True,
        )
        return User(id_=id_, props=full_props)

    def update_name(self, name: str) -> None:
        """Update user name with validation."""
        self.props.name = name

    def update_email(self, email: str) -> None:
        """Update user email with validation."""
        self.props.email = Email(email)

    def update_username(self, username: str) -> None:
        """Update username with validation."""
        self.props.username = username

    def make_active(self) -> None:
        """Make a user active"""
        self.props.is_active = True

    def make_inactive(self) -> None:
        """Make a user inactive"""
        self.props.is_active = False

    def validate(self) -> None:
        """Validate all user invariants."""
        if not self.props.name or not self.props.name.strip():
            raise ValueError("User name cannot be empty")
        if not self.props.email:
            raise ValueError("Email cannot be None")
        if not self.props.username or not self.props.username.strip():
            raise ValueError("Username cannot be empty")
        if not self.props.keycloak_id or not self.props.keycloak_id.strip():
            raise ValueError("Keycloak ID cannot be empty")
