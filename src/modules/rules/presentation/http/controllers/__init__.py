"""HTTP controllers for rules module."""

from .approve_rule import create_approve_rule_router
from .archive_rule import create_archive_rule_router
from .bulk_create_rules import create_bulk_create_rules_router
from .bulk_create_sections import create_bulk_create_sections_router
from .create_rule import create_create_rule_router
from .create_section import create_create_section_router
from .delete_rule import create_delete_rule_router
from .delete_section import create_delete_section_router
from .get_rule_activity_history import create_get_rule_activity_history_router
from .get_rule_by_id import create_get_rule_by_id_router
from .get_rule_by_slug import create_get_rule_by_slug_router
from .get_rule_sql import create_get_rule_sql_router
from .get_rules import create_get_rules_router
from .get_section_by_id import create_get_section_by_id_router
from .get_section_by_slug import create_get_section_by_slug_router
from .get_sections import create_get_sections_router
from .make_active_section import create_make_active_section_router
from .make_inactive_section import create_make_inactive_section_router
from .reject_rule import create_reject_rule_router
from .submit_rule_for_validation import create_submit_rule_for_validation_router
from .update_rule import create_update_rule_router
from .update_section import create_update_section_router

__all__ = [
    "create_approve_rule_router",
    "create_archive_rule_router",
    "create_bulk_create_rules_router",
    "create_bulk_create_sections_router",
    "create_create_rule_router",
    "create_create_section_router",
    "create_delete_rule_router",
    "create_delete_section_router",
    "create_get_rule_activity_history_router",
    "create_get_rule_by_id_router",
    "create_get_rule_by_slug_router",
    "create_get_rule_sql_router",
    "create_get_rules_router",
    "create_get_section_by_id_router",
    "create_get_section_by_slug_router",
    "create_get_sections_router",
    "create_make_active_section_router",
    "create_make_inactive_section_router",
    "create_reject_rule_router",
    "create_submit_rule_for_validation_router",
    "create_update_rule_router",
    "create_update_section_router",
]
