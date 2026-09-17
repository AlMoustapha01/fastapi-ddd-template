"""Report Entity - Domain Aggregate Root."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import uuid_utils.compat as uuid_utils

from core.lib.base.entity import Entity
from modules.reports.domain.value_objects import (
    ReportConfig,
    ReportConfigProps,
    ReportDescription,
    ReportId,
    ReportTitle,
    UserId,
)
from modules.rules.domain.enums import BalanceType, ProfileType


@dataclass
class ReportProps:
    """Properties of a Report entity."""

    title: ReportTitle
    description: ReportDescription
    profile_type: ProfileType
    balance_type: BalanceType
    config: ReportConfig
    created_by: UserId


@dataclass
class CreateReportProps:
    """Properties required to create a new Report."""

    title: str
    description: str
    profile_type: ProfileType
    balance_type: BalanceType
    config: ReportConfigProps
    created_by: UUID


class Report(Entity[ReportId, ReportProps]):
    """
    Report aggregate root.

    A Report represents a configuration of rules for generating reports
    based on profile type and balance type.
    """

    def __init__(
        self,
        *,
        id_: ReportId,
        props: ReportProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        super().__init__(
            id_=id_,
            props=props,
            created_at_=created_at_,
            updated_at_=updated_at_,
        )

    @staticmethod
    def create(props: CreateReportProps) -> "Report":
        """
        Factory method to create a new Report with default values.
        """
        id_ = ReportId(uuid_utils.uuid7())

        full_props = ReportProps(
            title=ReportTitle(props.title),
            description=ReportDescription(props.description),
            profile_type=props.profile_type,
            balance_type=props.balance_type,
            config=ReportConfig(props.config),
            created_by=UserId(props.created_by),
        )

        return Report(id_=id_, props=full_props)

    @staticmethod
    def reconstitute(
        *,
        id_: ReportId,
        props: ReportProps,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Report":
        """
        Reconstitute a Report from persistence without emitting events.

        Used by repositories when loading from database.
        """
        return Report(
            id_=id_,
            props=props,
            created_at_=created_at,
            updated_at_=updated_at,
        )

    def update_title(self, new_title: str) -> "Report":
        """Update report title."""
        self.props.title = ReportTitle(new_title)
        return self

    def update_description(self, new_description: str) -> "Report":
        """Update report description."""
        self.props.description = ReportDescription(new_description)
        return self

    def update_config(self, new_config: ReportConfigProps) -> "Report":
        """Update report configuration."""
        self.props.config = ReportConfig(new_config)
        return self

    def is_configuration_complete(self) -> bool:
        """Check if the configuration is complete."""
        return self.props.config.is_complete()

    def get_total_rules_count(self) -> int:
        """Get the total number of rules configured."""
        return self.props.config.total_rules_count

    def to_plain_object(self) -> dict[str, object]:
        """Convert to plain dictionary for serialization."""
        return {
            "id": self.id_.value,
            "title": self.props.title.value,
            "description": self.props.description.value,
            "profile_type": self.props.profile_type,
            "balance_type": self.props.balance_type,
            "config": self.props.config.to_plain_object(),
            "created_at": self.created_at_,
            "updated_at": self.updated_at_,
            "created_by": self.props.created_by.value,
        }

    def _ensure_cred_balance_only_for_hybrid(self) -> None:
        """CRED balance type is only available for HYBRID profile."""
        if (
            self.props.balance_type == BalanceType.CRED
            and self.props.profile_type != ProfileType.HYBRID
        ):
            raise ValueError("CRED balance type is only available for HYBRID profile")

    def _ensure_validate_title(self) -> None:
        """Validate that title is not empty."""
        if not self.props.title or not self.props.title.value:
            raise ValueError("Report title cannot be empty")

    def _ensure_validate_config(self) -> None:
        """Validate that config is not None."""
        if self.props.config is None:
            raise ValueError("Report config cannot be None")

    def validate(self) -> None:
        """Validate all report invariants."""
        self._ensure_validate_title()
        self._ensure_validate_config()
        self._ensure_cred_balance_only_for_hybrid()

    @property
    def title(self) -> ReportTitle:
        """Return the report title."""
        return self.props.title

    @property
    def description(self) -> ReportDescription:
        """Return the report description."""
        return self.props.description

    @property
    def profile_type(self) -> ProfileType:
        """Return the profile type."""
        return self.props.profile_type

    @property
    def balance_type(self) -> BalanceType:
        """Return the balance type."""
        return self.props.balance_type

    @property
    def config(self) -> ReportConfig:
        """Return the report configuration."""
        return self.props.config

    @property
    def created_by(self) -> UserId:
        """Return the user who created the report."""
        return self.props.created_by
