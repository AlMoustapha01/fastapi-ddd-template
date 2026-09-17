"""Mapper between User entity and UserModel."""

from core.lib.db.repository import EntityMapperPort
from modules.users.domain.user import User, UserProps
from modules.users.domain.value_objects import Email, UserId
from modules.users.infrastructure.models.user_model import UserModel


class UserMapper(EntityMapperPort[User, UserModel]):
    """Maps between User domain entity and UserModel ORM model."""

    def to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        return UserModel(
            id=entity.id_.value,
            name=entity.props.name,
            email=entity.props.email.value,
            username=entity.props.username,
            keycloak_id=entity.props.keycloak_id,
            is_active=entity.props.is_active,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity."""
        user_id = UserId(model.id)

        props = UserProps(
            name=model.name,
            email=Email(model.email),
            username=model.username,
            keycloak_id=model.keycloak_id,
            is_active=model.is_active,
        )

        return User(
            id_=user_id,
            props=props,
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
