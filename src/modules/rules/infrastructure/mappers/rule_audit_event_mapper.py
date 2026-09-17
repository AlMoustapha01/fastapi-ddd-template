"""
Mappers for converting between domain events and persistence models.

These mappers handle the translation between domain events
and the flat database representation for audit purposes.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import uuid_utils.compat as uuid_utils

from modules.rules.domain.enums import RuleEventType, RuleStatus
from modules.rules.domain.events import (
    RuleApprovedEvent,
    RuleArchivedEvent,
    RuleConfigUpdatedEvent,
    RuleCreatedEvent,
    RuleEvent,
    RuleFieldUpdatedEvent,
    RuleNameUpdatedEvent,
    RuleRejectedEvent,
    RuleStatusChangedEvent,
    RuleSubmittedForValidationEvent,
)
from modules.rules.infrastructure.models import RuleAuditEventModel


class RuleAuditEventMapper:
    """Mapper for Rule audit events."""

    @classmethod
    def to_persistence(cls, event: RuleEvent) -> dict[str, Any]:
        """
        Convert a domain event to a dictionary for persistence.

        Handles all event types and extracts relevant data.

        Args:
            event: The domain event to convert

        Returns:
            Dictionary with all fields needed for persistence
        """
        base_data = {
            "id": event.event_id,
            "rule_id": event.rule_id,
            "event_type": event.event_type,
            "performed_by_user_id": event.performed_by,
            "occurred_at": event.occurred_at,
            "reason": event.reason,
            "previous_status": None,
            "new_status": None,
            "changes": None,
            "created_at": datetime.now(UTC),
        }

        # Handle specific event types
        match event:
            case RuleCreatedEvent():
                base_data["new_status"] = RuleStatus.DRAFT
                base_data["changes"] = {
                    "name": event.name,
                    "balance_type": event.balance_type,
                    "profile_type": event.profile_type,
                    "database_table_name": event.database_table_name,
                    "section_id": str(event.section_id),
                    "config": event.config,
                }

            case RuleNameUpdatedEvent():
                base_data["changes"] = {
                    "name": {"old": event.old_name, "new": event.new_name},
                    "slug": {"old": event.old_slug, "new": event.new_slug},
                }

            case RuleConfigUpdatedEvent():
                base_data["changes"] = {
                    "config": {"old": event.old_config, "new": event.new_config}
                }

            case RuleFieldUpdatedEvent():
                base_data["changes"] = {
                    event.field_name: {
                        "old": event.old_value,
                        "new": event.new_value,
                    }
                }

            case RuleStatusChangedEvent():
                base_data["previous_status"] = event.previous_status
                base_data["new_status"] = event.new_status

            case RuleSubmittedForValidationEvent():
                base_data["previous_status"] = RuleStatus.DRAFT
                base_data["new_status"] = RuleStatus.TO_VALIDATE

            case RuleRejectedEvent():
                base_data["previous_status"] = RuleStatus.TO_VALIDATE
                base_data["new_status"] = RuleStatus.DRAFT
                base_data["reason"] = event.rejection_reason
                base_data["changes"] = {"rejection_reason": event.rejection_reason}

            case RuleApprovedEvent():
                base_data["previous_status"] = RuleStatus.TO_VALIDATE
                base_data["new_status"] = RuleStatus.IN_PRODUCTION

            case RuleArchivedEvent():
                base_data["previous_status"] = RuleStatus.IN_PRODUCTION
                base_data["new_status"] = RuleStatus.ARCHIVED

            case _:
                pass

        return base_data

    @classmethod
    def to_model(cls, event: RuleEvent) -> RuleAuditEventModel:
        """
        Convert a domain event to a SQLAlchemy model.

        Args:
            event: The domain event to convert

        Returns:
            SQLAlchemy model instance
        """
        data = cls.to_persistence(event)
        return RuleAuditEventModel(**data)

    @classmethod
    def to_domain_dict(cls, model: RuleAuditEventModel) -> dict[str, Any]:
        """
        Convert a SQLAlchemy model to a domain-friendly dictionary.

        Note: We return a dict instead of reconstructing the original event
        because audit events are primarily read-only and used for display.

        Args:
            model: The SQLAlchemy model to convert

        Returns:
            Dictionary with domain event data
        """
        return {
            "event_id": model.id,
            "rule_id": model.rule_id,
            "event_type": RuleEventType(model.event_type),
            "performed_by": model.performed_by_user_id,
            "occurred_at": model.occurred_at,
            "reason": model.reason,
            "previous_status": model.previous_status,
            "new_status": model.new_status,
            "changes": model.changes,
        }

    @classmethod
    def reconstruct_event(cls, model: RuleAuditEventModel) -> RuleEvent:  # noqa: PLR0911
        """
        Reconstruct a domain event from a SQLAlchemy model.

        This is useful when you need to replay events or work with the actual
        domain event objects rather than dictionaries.

        Args:
            model: The SQLAlchemy model to convert

        Returns:
            The reconstructed domain event

        Raises:
            ValueError: If the event type is unknown
        """
        event_type = RuleEventType(model.event_type)
        base_kwargs = {
            "rule_id": model.rule_id,
            "performed_by": model.performed_by_user_id,
            "reason": model.reason,
            "event_id": model.id,
            "occurred_at": model.occurred_at,
        }

        match event_type:
            case RuleEventType.CREATED:
                changes = model.changes or {}
                return RuleCreatedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    name=changes.get("name", ""),
                    balance_type=changes.get("balance_type", ""),
                    profile_type=changes.get("profile_type", ""),
                    section_id=UUID(changes.get("section_id", str(uuid_utils.uuid7()))),
                    database_table_name=changes.get("database_table_name", []),
                    config=changes.get("config", {}),
                )

            case RuleEventType.NAME_UPDATED:
                changes = model.changes or {}
                name_changes = changes.get("name", {})
                slug_changes = changes.get("slug", {})
                return RuleNameUpdatedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    old_name=name_changes.get("old", ""),
                    new_name=name_changes.get("new", ""),
                    old_slug=slug_changes.get("old", ""),
                    new_slug=slug_changes.get("new", ""),
                )

            case RuleEventType.CONFIG_UPDATED:
                changes = model.changes or {}
                config_changes = changes.get("config", {})
                return RuleConfigUpdatedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    old_config=config_changes.get("old", {}),
                    new_config=config_changes.get("new", {}),
                )

            case RuleEventType.UPDATED:
                changes = model.changes or {}
                # Get the first field name from changes
                field_name = next(iter(changes.keys()), "unknown")
                field_changes = changes.get(field_name, {})
                return RuleFieldUpdatedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    field_name=field_name,
                    old_value=field_changes.get("old"),
                    new_value=field_changes.get("new"),
                )

            case RuleEventType.STATUS_CHANGED:
                return RuleStatusChangedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    previous_status=model.previous_status or "",
                    new_status=model.new_status or "",
                )

            case RuleEventType.SUBMITTED_FOR_VALIDATION:
                return RuleSubmittedForValidationEvent(**base_kwargs)  # type: ignore[arg-type]

            case RuleEventType.REJECTED:
                return RuleRejectedEvent(
                    **base_kwargs,  # type: ignore[arg-type]
                    rejection_reason=model.reason or "",
                )

            case RuleEventType.APPROVED:
                return RuleApprovedEvent(**base_kwargs)  # type: ignore[arg-type]

            case RuleEventType.ARCHIVED:
                return RuleArchivedEvent(**base_kwargs)  # type: ignore[arg-type]

            case _:
                raise ValueError(f"Unknown event type: {event_type}")
