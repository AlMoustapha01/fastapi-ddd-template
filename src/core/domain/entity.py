"""Base class for domain entities."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from core.domain.identifier import EntityId


class Entity[TId: EntityId, TProps](ABC):
    """
    Object defined by its identity rather than by its attributes.

    - `id_` is read-only; entities are compared by type and `id_`.
    - `props` holds the mutable state; mutating methods must call `touch()`.
    - `validate()` runs once, at construction.
    """

    def __init__(
        self,
        *,
        id_: TId,
        props: TProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        self._id = id_
        self.props = props
        self.created_at_ = created_at_ or datetime.now(tz=UTC)
        self.updated_at_ = updated_at_ or self.created_at_
        self.validate()

    @property
    def id_(self) -> TId:
        return self._id

    def touch(self) -> None:
        """Record that the state of the entity changed."""
        self.updated_at_ = datetime.now(tz=UTC)

    @abstractmethod
    def validate(self) -> None:
        """Raise a `DomainError` when an invariant does not hold."""

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Entity)
            and type(self) is type(other)
            and self.id_ == other.id_
        )

    def __hash__(self) -> int:
        return hash((type(self), self._id))
