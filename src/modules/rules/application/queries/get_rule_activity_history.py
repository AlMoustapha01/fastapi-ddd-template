"""Get rule activity history query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID

from core.lib.db.repository.paginated import Paginated, PaginatedQueryParams
from modules.rules.domain.enums import RuleEventType
from modules.rules.domain.events import RuleEvent
from modules.rules.domain.exceptions import RuleNotFoundError
from modules.rules.domain.ports import RuleAuditRepositoryPort, RuleRepositoryPort
from modules.rules.domain.value_objects import RuleId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRuleActivityHistoryRequest:
    """Request to get rule activity history."""

    rule_id: UUID
    page: int = 1
    limit: int = 10


class ActivityEventResponse(TypedDict):
    """Single activity event response."""

    event_id: UUID
    event_type: str
    performed_by_user_id: UUID
    occurred_at: datetime
    reason: str | None
    previous_status: str | None
    new_status: str | None
    changes: dict[str, Any] | None


class RuleActivityHistoryResponse(TypedDict):
    """Paginated rule activity history response."""

    rule_id: UUID
    rule_name: str
    count: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    data: list[ActivityEventResponse]


class GetRuleActivityHistoryQuery:
    """Query to get the activity history of a rule."""

    def __init__(
        self,
        rule_repository: RuleRepositoryPort,
        audit_repository: RuleAuditRepositoryPort,
    ) -> None:
        self._rule_repository = rule_repository
        self._audit_repository = audit_repository

    async def execute(
        self, request: GetRuleActivityHistoryRequest
    ) -> RuleActivityHistoryResponse:
        """
        Execute the get rule activity history query.

        Returns a chronological list of all events that occurred on a rule,
        including who performed the action, when, and what changed.

        :param request: The request with rule ID and pagination
        :return: Rule activity history with events
        :raises RuleNotFoundError: When rule is not found
        """
        log.info(
            "Fetching activity history for rule: %s, page=%d, limit=%d",
            request.rule_id,
            request.page,
            request.limit,
        )

        # Verify rule exists
        rule_id = RuleId(request.rule_id)
        rule = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.rule_id)
            raise RuleNotFoundError(str(request.rule_id))

        # Build pagination params
        params = PaginatedQueryParams[RuleEvent](
            page=request.page,
            limit=request.limit,
        )

        # Fetch paginated audit events
        paginated: Paginated[
            RuleEvent
        ] = await self._audit_repository.find_all_paginated(
            params=params,
            rule_id=request.rule_id,
        )

        log.info(
            "Fetched %d events (page %d/%d) for rule %s",
            len(paginated.data),
            paginated.page,
            paginated.total_pages,
            request.rule_id,
        )

        # Map events to response format
        event_responses: list[ActivityEventResponse] = [
            ActivityEventResponse(
                event_id=event.event_id,
                event_type=event.event_type.value,
                performed_by_user_id=event.performed_by,
                occurred_at=event.occurred_at,
                reason=getattr(event, "reason", None),
                previous_status=self._get_previous_status(event.event_type),
                new_status=self._get_new_status(event.event_type),
                changes=self._extract_changes(event),
            )
            for event in paginated.data
        ]

        return RuleActivityHistoryResponse(
            rule_id=request.rule_id,
            rule_name=rule.props.name,
            count=paginated.count,
            limit=paginated.limit,
            page=paginated.page,
            total_pages=paginated.total_pages,
            has_next=paginated.has_next,
            has_previous=paginated.has_previous,
            data=event_responses,
        )

    def _extract_changes(self, event: Any) -> dict[str, Any] | None:
        """Extract changes from event based on event type."""
        event_type = event.event_type
        extractors = {
            RuleEventType.NAME_UPDATED: self._extract_name_changes,
            RuleEventType.CONFIG_UPDATED: self._extract_config_changes,
            RuleEventType.UPDATED: self._extract_field_changes,
            RuleEventType.STATUS_CHANGED: self._extract_status_changes,
            RuleEventType.REJECTED: self._extract_rejection_changes,
            RuleEventType.CREATED: self._extract_creation_changes,
        }
        extractor = extractors.get(event_type)
        if extractor:
            changes = extractor(event)
            return changes if changes else None
        return None

    def _extract_name_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for name update events."""
        changes: dict[str, Any] = {}
        if hasattr(event, "old_name") and hasattr(event, "new_name"):
            changes["name"] = {"old": event.old_name, "new": event.new_name}
        if hasattr(event, "old_slug") and hasattr(event, "new_slug"):
            changes["slug"] = {"old": event.old_slug, "new": event.new_slug}
        return changes

    def _extract_config_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for config update events."""
        if hasattr(event, "old_config") and hasattr(event, "new_config"):
            return {"config": {"old": event.old_config, "new": event.new_config}}
        return {}

    def _extract_field_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for generic field update events."""
        if hasattr(event, "field_name"):
            return {
                event.field_name: {
                    "old": getattr(event, "old_value", None),
                    "new": getattr(event, "new_value", None),
                }
            }
        return {}

    def _extract_status_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for status change events."""
        if hasattr(event, "previous_status") and hasattr(event, "new_status"):
            return {
                "previous_status": event.previous_status,
                "new_status": event.new_status,
            }
        return {}

    def _extract_rejection_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for rejection events."""
        if hasattr(event, "rejection_reason"):
            return {"rejection_reason": event.rejection_reason}
        return {}

    def _extract_creation_changes(self, event: Any) -> dict[str, Any]:
        """Extract changes for creation events."""
        changes: dict[str, Any] = {}
        attrs = [
            "name",
            "balance_type",
            "profile_type",
            "database_table_name",
            "config",
        ]
        for attr in attrs:
            if hasattr(event, attr):
                changes[attr] = getattr(event, attr)
        if hasattr(event, "section_id"):
            changes["section_id"] = str(event.section_id)
        return changes

    def _get_previous_status(self, event_type: RuleEventType) -> str | None:
        """Get the previous status based on event type."""
        status_map = {
            RuleEventType.CREATED: None,
            RuleEventType.SUBMITTED_FOR_VALIDATION: "draft",
            RuleEventType.REJECTED: "to_validate",
            RuleEventType.APPROVED: "to_validate",
            RuleEventType.ARCHIVED: "in_production",
        }
        return status_map.get(event_type)

    def _get_new_status(self, event_type: RuleEventType) -> str | None:
        """Get the new status based on event type."""
        status_map = {
            RuleEventType.CREATED: "draft",
            RuleEventType.SUBMITTED_FOR_VALIDATION: "to_validate",
            RuleEventType.REJECTED: "draft",
            RuleEventType.APPROVED: "in_production",
            RuleEventType.ARCHIVED: "archived",
        }
        return status_map.get(event_type)
