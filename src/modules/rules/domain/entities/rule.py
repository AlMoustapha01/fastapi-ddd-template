"""Rule Entity - Domain Aggregate Root with event sourcing capabilities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

import uuid_utils.compat as uuid_utils

from core.lib.base.entity import Entity
from modules.rules.domain.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.domain.events import (
    RuleApprovedEvent,
    RuleArchivedEvent,
    RuleConfigUpdatedEvent,
    RuleCreatedEvent,
    RuleNameUpdatedEvent,
    RuleRejectedEvent,
    RuleSubmittedForValidationEvent,
)
from modules.rules.domain.events.rule_events import RuleEvent
from modules.rules.domain.exceptions import RuleInvalidStatusError
from modules.rules.domain.value_objects import (
    RuleConfig,
    RuleId,
    SectionId,
    SlugValueObject,
    UserId,
)

# ----------------------------------------------------
# Constants
# ----------------------------------------------------
MAX_NAME_LENGTH = 255

# ----------------------------------------------------
# State Machine : valid transitions between statuses
# ----------------------------------------------------
ALLOWED_TRANSITIONS: dict[RuleStatus, list[RuleStatus]] = {
    RuleStatus.DRAFT: [RuleStatus.TO_VALIDATE],
    RuleStatus.TO_VALIDATE: [RuleStatus.IN_PRODUCTION, RuleStatus.DRAFT],
    RuleStatus.IN_PRODUCTION: [RuleStatus.ARCHIVED],
    RuleStatus.ARCHIVED: [],
}


@dataclass
class RuleProps:
    """Properties of a Rule entity."""

    name: str
    slug: SlugValueObject
    database_table_name: list[str]
    config: RuleConfig
    balance_type: BalanceType
    profile_type: ProfileType
    section_id: SectionId
    status: RuleStatus
    created_by: UserId
    last_modified_by: UserId | None = None


@dataclass
class CreateRuleProps:
    """Properties required to create a new Rule."""

    name: str
    database_table_name: list[str]
    config: RuleConfig
    balance_type: BalanceType
    profile_type: ProfileType
    section_id: SectionId
    created_by: UUID


class Rule(Entity[RuleId, RuleProps]):  # noqa: PLR0904
    """
    Rule aggregate root with full audit trail.

    All mutations emit domain events that can be persisted for audit purposes.
    The rule follows a strict state machine for status transitions.
    """

    def __init__(
        self,
        *,
        id_: RuleId,
        props: RuleProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        super().__init__(
            id_=id_,
            props=props,
            created_at_=created_at_,
            updated_at_=updated_at_,
        )
        self._domain_events: list[RuleEvent] = []
        self.validate()

    # ----------------------------------------------------
    # Domain Events Management
    # ----------------------------------------------------
    @property
    def domain_events(self) -> list[RuleEvent]:
        """Return a copy of pending domain events."""
        return self._domain_events.copy()

    def add_event(self, event: RuleEvent) -> None:
        """Add a domain event to be dispatched."""
        self._domain_events.append(event)

    def clear_events(self) -> None:
        """Clear all pending domain events."""
        self._domain_events.clear()

    def pop_events(self) -> list[RuleEvent]:
        """Return and clear all pending domain events."""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    @staticmethod
    def create(props: CreateRuleProps) -> "Rule":
        """
        Factory method to create a new Rule with default values.

        Emits a RuleCreatedEvent for audit purposes.
        """
        id_ = RuleId(uuid_utils.uuid7())

        full_props = RuleProps(
            name=props.name,
            slug=SlugValueObject.from_text(props.name),
            database_table_name=props.database_table_name,
            config=props.config,
            balance_type=props.balance_type,
            profile_type=props.profile_type,
            section_id=props.section_id,
            status=RuleStatus.DRAFT,
            created_by=UserId(props.created_by),
            last_modified_by=None,
        )

        rule = Rule(id_=id_, props=full_props)

        # Emit creation event
        rule.add_event(
            RuleCreatedEvent.create(
                rule_id=id_.value,
                created_by=props.created_by,
                name=props.name,
                balance_type=props.balance_type.value,
                profile_type=props.profile_type.value,
                section_id=props.section_id.value,
                database_table_name=props.database_table_name,
                config=props.config.to_dict(),
            )
        )

        return rule

    @staticmethod
    def reconstitute(
        *,
        id_: RuleId,
        props: RuleProps,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Rule":
        """
        Reconstitute a Rule from persistence without emitting events.

        Used by repositories when loading from database.
        """
        return Rule(
            id_=id_,
            props=props,
            created_at_=created_at,
            updated_at_=updated_at,
        )

    def _can_transition_to(self, new_status: RuleStatus) -> bool:
        """Check if transition to new status is allowed."""
        current_status = self.props.status
        allowed = ALLOWED_TRANSITIONS.get(current_status, [])
        return new_status in allowed

    def _ensure_can_modify(self) -> None:
        """Ensure the rule can be modified (only in DRAFT status)."""
        if self.props.status != RuleStatus.DRAFT:
            raise RuleInvalidStatusError(
                rule_id=str(self.id_.value),
                current_status=self.props.status.value,
                allowed_statuses=[RuleStatus.DRAFT.value],
                operation="modify",
            )

    def submit_for_validation(self, by_user: UUID, reason: str | None = None) -> None:
        """
        Submit the rule for validation.

        Only allowed from DRAFT status.
        Emits RuleSubmittedForValidationEvent.
        """
        if not self._can_transition_to(RuleStatus.TO_VALIDATE):
            raise ValueError(
                f"Cannot submit for validation from status {self.props.status.value}"
            )

        self.props.status = RuleStatus.TO_VALIDATE
        self.props.last_modified_by = UserId(by_user)

        self.add_event(
            RuleSubmittedForValidationEvent.create(
                rule_id=self.id_.value,
                submitted_by=by_user,
                reason=reason,
            )
        )

    def reject(self, by_user: UUID, reason: str) -> None:
        """
        Reject the rule and send it back to draft.

        Only allowed from TO_VALIDATE status.
        Requires a rejection reason.
        Emits RuleRejectedEvent.
        """
        if not self._can_transition_to(RuleStatus.DRAFT):
            raise ValueError(f"Cannot reject from status {self.props.status.value}")

        if not reason or not reason.strip():
            raise ValueError("Rejection reason is required")

        self.props.status = RuleStatus.DRAFT
        self.props.last_modified_by = UserId(by_user)

        self.add_event(
            RuleRejectedEvent.create(
                rule_id=self.id_.value,
                rejected_by=by_user,
                rejection_reason=reason,
            )
        )

    def approve(self, by_user: UUID, reason: str | None = None) -> None:
        """
        Approve the rule and put it in production.

        Only allowed from TO_VALIDATE status.
        Emits RuleApprovedEvent.
        """
        if not self._can_transition_to(RuleStatus.IN_PRODUCTION):
            raise ValueError(f"Cannot approve from status {self.props.status.value}")

        self.props.status = RuleStatus.IN_PRODUCTION
        self.props.last_modified_by = UserId(by_user)

        self.add_event(
            RuleApprovedEvent.create(
                rule_id=self.id_.value,
                approved_by=by_user,
                reason=reason,
            )
        )

    def archive(self, by_user: UUID, reason: str | None = None) -> None:
        """
        Archive the rule.

        Only allowed from IN_PRODUCTION status.
        Once archived, no further transitions are allowed.
        Emits RuleArchivedEvent.
        """
        if not self._can_transition_to(RuleStatus.ARCHIVED):
            raise ValueError(f"Cannot archive from status {self.props.status.value}")

        self.props.status = RuleStatus.ARCHIVED
        self.props.last_modified_by = UserId(by_user)

        self.add_event(
            RuleArchivedEvent.create(
                rule_id=self.id_.value,
                archived_by=by_user,
                reason=reason,
            )
        )

    def update_name(self, name: str, by_user: UUID, reason: str | None = None) -> None:
        """
        Update rule name and regenerate slug.

        Only allowed in DRAFT status.
        Emits RuleNameUpdatedEvent.
        """
        self._ensure_can_modify()

        old_name = self.props.name
        old_slug = str(self.props.slug)

        self.props.name = name
        self.props.slug = SlugValueObject.from_text(name)
        self.props.last_modified_by = UserId(by_user)

        self._ensure_validate_name()
        self._ensure_validate_slug()

        self.add_event(
            RuleNameUpdatedEvent.create(
                rule_id=self.id_.value,
                updated_by=by_user,
                old_name=old_name,
                new_name=name,
                old_slug=old_slug,
                new_slug=str(self.props.slug),
                reason=reason,
            )
        )

    def update_database_table_name(
        self, database_table_name: list[str], by_user: UUID
    ) -> None:
        """Update database table names. Only allowed in DRAFT status."""
        self._ensure_can_modify()
        self.props.database_table_name = database_table_name
        self.props.last_modified_by = UserId(by_user)

    def update_balance_type(self, balance_type: BalanceType, by_user: UUID) -> None:
        """Update balance type with validation. Only allowed in DRAFT status."""
        self._ensure_can_modify()
        self.props.balance_type = balance_type
        self.props.last_modified_by = UserId(by_user)
        self._ensure_prepaid_profile_has_only_main_balance()

    def update_profile_type(self, profile_type: ProfileType, by_user: UUID) -> None:
        """Update profile type with validation. Only allowed in DRAFT status."""
        self._ensure_can_modify()
        self.props.profile_type = profile_type
        self.props.last_modified_by = UserId(by_user)
        self._ensure_prepaid_profile_has_only_main_balance()

    def update_section_id(self, section_id: UUID, by_user: UUID) -> None:
        """Update section association. Only allowed in DRAFT status."""
        self._ensure_can_modify()
        self.props.section_id = SectionId(section_id)
        self.props.last_modified_by = UserId(by_user)

    def update_config(
        self, config: dict[str, Any], by_user: UUID, reason: str | None = None
    ) -> None:
        """
        Update rule configuration with validation.

        Only allowed in DRAFT status.
        Emits RuleConfigUpdatedEvent.
        """
        self._ensure_can_modify()

        old_config = self.props.config.to_dict()
        new_config = RuleConfig.from_dict(config)

        self.props.config = new_config
        self.props.last_modified_by = UserId(by_user)

        self._ensure_validate_config()
        self._ensure_rule_has_valid_configuration()

        self.add_event(
            RuleConfigUpdatedEvent.create(
                rule_id=self.id_.value,
                updated_by=by_user,
                old_config=old_config,
                new_config=config,
                reason=reason,
            )
        )

    def _ensure_validate_name(self) -> None:
        """Validate that name is not empty and has reasonable length."""
        if not self.props.name or not self.props.name.strip():
            raise ValueError("Rule name cannot be empty")
        if len(self.props.name) > MAX_NAME_LENGTH:
            raise ValueError(f"Rule name cannot exceed {MAX_NAME_LENGTH} characters")

    def _ensure_validate_slug(self) -> None:
        """Validate that slug is not empty and matches the name."""
        if not self.props.slug:
            raise ValueError("Slug cannot be empty")
        expected_slug = SlugValueObject.from_text(self.props.name)
        if self.props.slug != expected_slug:
            raise ValueError("Slug is not valid for the given name")

    def _ensure_validate_config(self) -> None:
        """Validate that config is not None."""
        if self.props.config is None:
            raise ValueError("Rule config cannot be None")

    def _ensure_prepaid_profile_has_only_main_balance(self) -> None:
        """Prepaid profile can only have main balance."""
        if (
            self.props.profile_type == ProfileType.PREPAID
            and self.props.balance_type != BalanceType.MAIN_BALANCE
        ):
            raise ValueError("Prepaid profile can only have main balance")

    def _ensure_rule_has_valid_configuration(self) -> None:
        """A rule must have a valid SQL configuration."""
        if not self.props.name or not self.props.name.strip():
            raise ValueError("A rule must have a name")

        if not self.props.config:
            raise ValueError("A rule must have a configuration")

        self.props.config.validate()

    def validate(self) -> None:
        """Validate all rule invariants."""
        self._ensure_validate_name()
        self._ensure_validate_slug()
        self._ensure_validate_config()
        self._ensure_prepaid_profile_has_only_main_balance()
        self._ensure_rule_has_valid_configuration()

    # ----------------------------------------------------
    # Convenience Properties
    # ----------------------------------------------------
    @property
    def is_draft(self) -> bool:
        return self.props.status == RuleStatus.DRAFT

    @property
    def is_pending_validation(self) -> bool:
        return self.props.status == RuleStatus.TO_VALIDATE

    @property
    def is_in_production(self) -> bool:
        return self.props.status == RuleStatus.IN_PRODUCTION

    @property
    def is_archived(self) -> bool:
        return self.props.status == RuleStatus.ARCHIVED

    @property
    def can_be_modified(self) -> bool:
        return self.props.status == RuleStatus.DRAFT
