"""Rule event types enumeration."""

from enum import StrEnum


class RuleEventType(StrEnum):
    """Types of events that can occur on a Rule."""

    CREATED = "rule_created"
    UPDATED = "rule_updated"
    NAME_UPDATED = "rule_name_updated"
    CONFIG_UPDATED = "rule_config_updated"
    STATUS_CHANGED = "rule_status_changed"
    SUBMITTED_FOR_VALIDATION = "rule_submitted_for_validation"
    REJECTED = "rule_rejected"
    APPROVED = "rule_approved"
    ARCHIVED = "rule_archived"
