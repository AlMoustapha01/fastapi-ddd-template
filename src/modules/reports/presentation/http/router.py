"""Main router for reports module."""

from fastapi import APIRouter

from .controllers import (
    create_create_report_router,
    create_delete_report_router,
    create_get_report_by_id_router,
    create_get_reports_router,
    create_update_report_router,
)


def create_reports_router() -> APIRouter:
    """
    Create the main router for reports module.

    Returns:
        APIRouter with all reports endpoints
    """
    # Report endpoints
    reports_router = APIRouter(prefix="/reports", tags=["Reports"])
    reports_router.include_router(create_get_reports_router())
    reports_router.include_router(create_get_report_by_id_router())
    reports_router.include_router(create_create_report_router())
    reports_router.include_router(create_update_report_router())
    reports_router.include_router(create_delete_report_router())

    # Main router
    router = APIRouter()
    router.include_router(reports_router)

    return router
