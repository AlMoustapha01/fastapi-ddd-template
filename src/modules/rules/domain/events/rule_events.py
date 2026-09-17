"""
Domain Events for the Rules module.

These events capture meaningful occurrences in the Rule aggregate lifecycle.
They are used for:
- Audit trail persistence
- Event-driven integrations
- CQRS read model updates
"""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from core.lib.base.domain_event import DomainEvent
from modules.rules.domain.enums import RuleEventType


# ----------------------------------------------------
# Base Rule Event
# ----------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class RuleEvent(DomainEvent):
    """Base class for all Rule-related domain events."""

    rule_id: UUID
    performed_by: UUID
    event_type: RuleEventType
    reason: str | None = None

    @property
    def aggregate_id(self) -> UUID:
        return self.rule_id


# ----------------------------------------------------
# Creation Events
# ----------------------------------------------------
@dataclass(frozen=True)
class RuleCreatedEvent(RuleEvent):
    """Event emitted when a new Rule is created."""

    name: str
    balance_type: str
    profile_type: str
    section_id: UUID
    database_table_name: list[str]
    config: dict[str, Any]
    event_type: RuleEventType = field(default=RuleEventType.CREATED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        created_by: UUID,
        name: str,
        balance_type: str,
        profile_type: str,
        section_id: UUID,
        database_table_name: list[str],
        config: dict[str, Any],
    ) -> "RuleCreatedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=created_by,
            name=name,
            balance_type=balance_type,
            profile_type=profile_type,
            section_id=section_id,
            database_table_name=database_table_name,
            config=config,
        )


# ----------------------------------------------------
# Update Events
# ----------------------------------------------------
@dataclass(frozen=True)
class RuleFieldUpdatedEvent(RuleEvent):
    """Event emitted when a Rule field is updated."""

    field_name: str
    old_value: Any
    new_value: Any
    event_type: RuleEventType = field(default=RuleEventType.UPDATED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        updated_by: UUID,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: str | None = None,
    ) -> "RuleFieldUpdatedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=updated_by,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
        )


@dataclass(frozen=True)
class RuleNameUpdatedEvent(RuleEvent):
    """Event emitted when a Rule's name is updated."""

    old_name: str
    new_name: str
    old_slug: str
    new_slug: str
    event_type: RuleEventType = field(default=RuleEventType.NAME_UPDATED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        updated_by: UUID,
        old_name: str,
        new_name: str,
        old_slug: str,
        new_slug: str,
        reason: str | None = None,
    ) -> "RuleNameUpdatedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=updated_by,
            old_name=old_name,
            new_name=new_name,
            old_slug=old_slug,
            new_slug=new_slug,
            reason=reason,
        )


@dataclass(frozen=True)
class RuleConfigUpdatedEvent(RuleEvent):
    """Event emitted when a Rule's configuration is updated."""

    old_config: dict[str, Any]
    new_config: dict[str, Any]
    event_type: RuleEventType = field(default=RuleEventType.CONFIG_UPDATED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        updated_by: UUID,
        old_config: dict[str, Any],
        new_config: dict[str, Any],
        reason: str | None = None,
    ) -> "RuleConfigUpdatedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=updated_by,
            old_config=old_config,
            new_config=new_config,
            reason=reason,
        )


# ----------------------------------------------------
# Status Transition Events
# ----------------------------------------------------
@dataclass(frozen=True)
class RuleStatusChangedEvent(RuleEvent):
    """Base event for status changes."""

    previous_status: str
    new_status: str
    event_type: RuleEventType = field(default=RuleEventType.STATUS_CHANGED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        changed_by: UUID,
        previous_status: str,
        new_status: str,
        reason: str | None = None,
    ) -> "RuleStatusChangedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=changed_by,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
        )


@dataclass(frozen=True)
class RuleSubmittedForValidationEvent(RuleEvent):
    """Event emitted when a Rule is submitted for validation."""

    event_type: RuleEventType = field(
        default=RuleEventType.SUBMITTED_FOR_VALIDATION, init=False
    )

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        submitted_by: UUID,
        reason: str | None = None,
    ) -> "RuleSubmittedForValidationEvent":
        return cls(
            rule_id=rule_id,
            performed_by=submitted_by,
            reason=reason,
        )


@dataclass(frozen=True)
class RuleRejectedEvent(RuleEvent):
    """Event emitted when a Rule is rejected (sent back to draft)."""

    rejection_reason: str
    event_type: RuleEventType = field(default=RuleEventType.REJECTED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        rejected_by: UUID,
        rejection_reason: str,
    ) -> "RuleRejectedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=rejected_by,
            rejection_reason=rejection_reason,
            reason=rejection_reason,
        )


@dataclass(frozen=True)
class RuleApprovedEvent(RuleEvent):
    """Event emitted when a Rule is approved and put in production."""

    event_type: RuleEventType = field(default=RuleEventType.APPROVED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        approved_by: UUID,
        reason: str | None = None,
    ) -> "RuleApprovedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=approved_by,
            reason=reason,
        )


@dataclass(frozen=True)
class RuleArchivedEvent(RuleEvent):
    """Event emitted when a Rule is archived."""

    event_type: RuleEventType = field(default=RuleEventType.ARCHIVED, init=False)

    @classmethod
    def create(
        cls,
        rule_id: UUID,
        archived_by: UUID,
        reason: str | None = None,
    ) -> "RuleArchivedEvent":
        return cls(
            rule_id=rule_id,
            performed_by=archived_by,
            reason=reason,
        )
