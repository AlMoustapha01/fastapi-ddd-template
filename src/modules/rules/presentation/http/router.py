"""Main router for rules module."""

from fastapi import APIRouter

from .controllers import (
    create_approve_rule_router,
    create_archive_rule_router,
    create_bulk_create_rules_router,
    create_bulk_create_sections_router,
    create_create_rule_router,
    create_create_section_router,
    create_delete_rule_router,
    create_delete_section_router,
    create_get_rule_activity_history_router,
    create_get_rule_by_id_router,
    create_get_rule_by_slug_router,
    create_get_rule_sql_router,
    create_get_rules_router,
    create_get_section_by_id_router,
    create_get_section_by_slug_router,
    create_get_sections_router,
    create_make_active_section_router,
    create_make_inactive_section_router,
    create_reject_rule_router,
    create_submit_rule_for_validation_router,
    create_update_rule_router,
    create_update_section_router,
)


def create_rules_router() -> APIRouter:
    """
    Create the main router for rules module.

    Returns:
        APIRouter with all rules endpoints
    """
    # Section endpoints
    sections_router = APIRouter(prefix="/sections", tags=["Sections"])
    sections_router.include_router(create_get_sections_router())
    sections_router.include_router(create_get_section_by_id_router())
    sections_router.include_router(create_get_section_by_slug_router())
    sections_router.include_router(create_create_section_router())
    sections_router.include_router(create_bulk_create_sections_router())
    sections_router.include_router(create_make_active_section_router())
    sections_router.include_router(create_make_inactive_section_router())
    sections_router.include_router(create_update_section_router())
    sections_router.include_router(create_delete_section_router())

    # Rule endpoints
    rules_router = APIRouter(prefix="/rules", tags=["Rules"])
    rules_router.include_router(create_get_rules_router())
    rules_router.include_router(create_get_rule_by_id_router())
    rules_router.include_router(create_get_rule_by_slug_router())
    rules_router.include_router(create_get_rule_sql_router())
    rules_router.include_router(create_get_rule_activity_history_router())
    rules_router.include_router(create_create_rule_router())
    rules_router.include_router(create_bulk_create_rules_router())
    rules_router.include_router(create_delete_rule_router())
    rules_router.include_router(create_update_rule_router())
    # Rule workflow endpoints
    rules_router.include_router(create_submit_rule_for_validation_router())
    rules_router.include_router(create_approve_rule_router())
    rules_router.include_router(create_reject_rule_router())
    rules_router.include_router(create_archive_rule_router())

    # Main router
    router = APIRouter()
    router.include_router(sections_router)
    router.include_router(rules_router)

    return router
