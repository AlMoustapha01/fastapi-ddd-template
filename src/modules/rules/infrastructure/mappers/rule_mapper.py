"""Mapper between Rule entity and RuleModel."""

from core.lib.db.repository import EntityMapperPort
from modules.rules.domain.entities.rule import Rule, RuleProps
from modules.rules.domain.value_objects import (
    RuleConfig,
    RuleId,
    SectionId,
    SlugValueObject,
    UserId,
)
from modules.rules.infrastructure.models.rule_model import RuleModel


class RuleMapper(EntityMapperPort[Rule, RuleModel]):
    """Maps between Rule domain entity and RuleModel ORM model."""

    def to_model(self, entity: Rule) -> RuleModel:
        """Convert Rule entity to RuleModel."""
        return RuleModel(
            id=entity.id_.value,
            name=entity.props.name,
            slug=entity.props.slug.value,
            profile_type=entity.props.profile_type,
            balance_type=entity.props.balance_type,
            section_id=entity.props.section_id.value,
            database_table_name=entity.props.database_table_name,
            config=entity.props.config.to_dict(),  # Convert RuleConfig to dict
            status=entity.props.status,
            created_by_user_id=entity.props.created_by.value,
            last_modified_by_user_id=(
                entity.props.last_modified_by.value
                if entity.props.last_modified_by
                else None
            ),
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: RuleModel) -> Rule:
        """
        Convert RuleModel to Rule entity using reconstitute.

        Avoids emitting events.
        """
        rule_id = RuleId(model.id)

        props = RuleProps(
            name=model.name,
            slug=SlugValueObject(model.slug),
            profile_type=model.profile_type,
            balance_type=model.balance_type,
            section_id=SectionId(model.section_id),  # Convert UUID to SectionId
            database_table_name=model.database_table_name,
            config=RuleConfig.from_dict(model.config),  # Convert dict to RuleConfig
            status=model.status,
            created_by=UserId(model.created_by_user_id),
            last_modified_by=(
                UserId(model.last_modified_by_user_id)
                if model.last_modified_by_user_id
                else None
            ),
        )

        return Rule.reconstitute(
            id_=rule_id,
            props=props,
            created_at=model.created_at,
            updated_at=model.updated_at or model.created_at,
        )
