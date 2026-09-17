from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Self, cast

from .value_object import ValueObject


class Entity[T: ValueObject, P](ABC):
    """
    Base class for domain entities, defined by a unique identity (`id`).
    - `id`: Identity that remains constant throughout the entity's lifecycle.
    - Entities are mutable, but are compared solely by their `id`.
    """

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        if cls is Entity:
            raise TypeError("Base Entity cannot be instantiated directly.")
        return object.__new__(cls)

    def __init__(
        self,
        *,
        id_: T,
        props: P,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        self.id_ = id_
        self.props = props
        self.created_at_ = created_at_ or datetime.now(tz=UTC)
        self.updated_at_ = updated_at_ or datetime.now(tz=UTC)
        self.validate()

    def __setattr__(self, name: str, value: Any) -> None:
        """
        - Prevents modifying the `id` after it's set.
        - Updates `updated_at` whenever `props` or other attributes change.
        """
        if name == "id_" and getattr(self, "id_", None) is not None:
            raise AttributeError("Changing entity ID is not permitted.")
        object.__setattr__(self, name, value)

        if name not in {"id_", "created_at_", "updated_at_"}:
            object.__setattr__(self, "updated_at_", datetime.now(tz=UTC))

    def __eq__(self, other: object) -> bool:
        """
        Two entities are considered equal if they have the same `id`,
        regardless of other attribute values.
        """
        return type(self) is type(other) and cast(Self, other).id_ == self.id_

    def __hash__(self) -> int:
        """
        Generate a hash based on entity type and the immutable `id`.
        This allows entities to be used in hash-based collections and
        reduces the risk of hash collisions between different entity types.
        """
        return hash((type(self), self.id_))

    @abstractmethod
    def validate(self) -> None:
        """
        Must be implemented by subclasses.
        Defines business invariants that must hold true for the entity.
        """
        ...
