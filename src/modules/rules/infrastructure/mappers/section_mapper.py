"""Mapper between Section entity and SectionModel."""

from core.lib.db.repository import EntityMapperPort
from modules.rules.domain.entities.section import Section, SectionProps
from modules.rules.domain.value_objects import SectionId, SlugValueObject
from modules.rules.infrastructure.models.section_model import SectionModel


class SectionMapper(EntityMapperPort[Section, SectionModel]):
    """Maps between Section domain entity and SectionModel ORM model."""

    def to_model(self, entity: Section) -> SectionModel:
        """Convert Section entity to SectionModel."""
        return SectionModel(
            id=entity.id_.value,
            name=entity.props.name,
            slug=entity.props.slug.value,
            description=entity.props.description,
            status=entity.props.status,
            created_by_user_id=entity.props.created_by_user_id,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: SectionModel) -> Section:
        """Convert SectionModel to Section entity."""
        section_id = SectionId(model.id)

        props = SectionProps(
            name=model.name,
            slug=SlugValueObject(model.slug),
            description=model.description,
            status=model.status,
            created_by_user_id=model.created_by_user_id,
        )

        return Section(
            id_=section_id,
            props=props,
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
