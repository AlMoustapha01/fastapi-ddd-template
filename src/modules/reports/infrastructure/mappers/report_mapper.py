"""Mapper between Report entity and ReportModel."""

from core.lib.db.repository import EntityMapperPort
from modules.reports.domain.entities.report import Report, ReportProps
from modules.reports.domain.value_objects import (
    ReportConfig,
    ReportConfigProps,
    ReportDescription,
    ReportId,
    ReportTitle,
    UserId,
)
from modules.reports.infrastructure.models.report_model import ReportModel


class ReportMapper(EntityMapperPort[Report, ReportModel]):
    """Maps between Report domain entity and ReportModel ORM model."""

    def to_model(self, entity: Report) -> ReportModel:
        """Convert Report entity to ReportModel."""

        return ReportModel(
            id=entity.id_.value,
            title=entity.props.title.value,
            description=entity.props.description.value,
            profile_type=entity.props.profile_type,
            balance_type=entity.props.balance_type,
            config=entity.props.config.to_plain_object(),
            created_by_user_id=entity.props.created_by.value,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: ReportModel) -> Report:
        """
        Convert ReportModel to Report entity using reconstitute.

        Avoids emitting events.
        """
        report_id = ReportId(model.id)

        # Convert config dict to ReportConfigProps
        config_props = ReportConfigProps(
            initial_credit_rule_id=model.config.get("initial_credit_rule_id", ""),
            final_credit_rule_id=model.config.get("final_credit_rule_id", ""),
            recharge_rules_ids=model.config.get("recharge_rules_ids", []),
            consumption_rules_ids=model.config.get("consumption_rules_ids", []),
        )

        props = ReportProps(
            title=ReportTitle(model.title),
            description=ReportDescription(model.description),
            profile_type=model.profile_type,
            balance_type=model.balance_type,
            config=ReportConfig(config_props),
            created_by=UserId(model.created_by_user_id),
        )

        return Report.reconstitute(
            id_=report_id,
            props=props,
            created_at=model.created_at,
            updated_at=model.updated_at or model.created_at,
        )
