from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid_utils

from core.lib.base.entity import Entity
from modules.rules.domain.enums import SectionStatus
from modules.rules.domain.value_objects import SectionId, SlugValueObject

# ----------------------------------------------------
# Constants
# ----------------------------------------------------
MAX_NAME_LENGTH = 255


@dataclass
class SectionProps:
    name: str
    slug: SlugValueObject
    description: str
    status: SectionStatus
    created_by_user_id: UUID


@dataclass
class CreateSectionProps:
    name: str
    description: str
    created_by_user_id: UUID


class Section(Entity[SectionId, SectionProps]):
    def __init__(
        self,
        *,
        id_: SectionId,
        props: SectionProps,
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
    def create(props: CreateSectionProps) -> "Section":
        """Factory method to create a new Section with default values."""
        id_ = SectionId(uuid_utils.uuid7())

        full_props = SectionProps(
            name=props.name,
            slug=SlugValueObject.from_text(props.name),
            description=props.description,
            status=SectionStatus.ACTIVE,
            created_by_user_id=props.created_by_user_id,
        )
        return Section(id_=id_, props=full_props)

    def update_name(self, name: str) -> None:
        """Update section name and regenerate slug with validation."""
        self.props.name = name
        self.props.slug = SlugValueObject.from_text(name)
        self._ensure_validate_name()
        self._ensure_validate_slug()

    def update_description(self, description: str) -> None:
        """Update section description with validation."""
        self.props.description = description
        self._ensure_validate_description()

    def make_inactive(self) -> None:
        """Set section status to inactive."""
        self.props.status = SectionStatus.INACTIVE

    def make_active(self) -> None:
        """Set section status to active."""
        self.props.status = SectionStatus.ACTIVE

    def _ensure_validate_name(self) -> None:
        """Validate that name is not empty and has reasonable length."""
        if not self.props.name or not self.props.name.strip():
            raise ValueError("Section name cannot be empty")
        if len(self.props.name) > MAX_NAME_LENGTH:
            raise ValueError(f"Section name cannot exceed {MAX_NAME_LENGTH} characters")

    def _ensure_validate_slug(self) -> None:
        """Validate that slug is not empty and matches the name."""
        if not self.props.slug:
            raise ValueError("Slug cannot be empty")
        expected_slug = SlugValueObject.from_text(self.props.name)
        if self.props.slug != expected_slug:
            raise ValueError("Slug is not valid for the given name")

    def _ensure_validate_description(self) -> None:
        """Validate that description is not empty."""
        if not self.props.description or not self.props.description.strip():
            raise ValueError("Section description cannot be empty")

    def validate(self) -> None:
        """Validate all section invariants."""
        self._ensure_validate_name()
        self._ensure_validate_slug()
        self._ensure_validate_description()
