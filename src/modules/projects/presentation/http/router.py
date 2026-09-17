"""HTTP router of the projects module."""

from fastapi import APIRouter

from modules.projects.presentation.http.controllers import (
    create_archive_project_router,
    create_create_project_router,
    create_delete_project_router,
    create_get_project_router,
    create_list_projects_router,
    create_update_project_router,
)


def create_projects_router() -> APIRouter:
    router = APIRouter(tags=["Projects"])
    for sub_router in (
        create_create_project_router(),
        create_list_projects_router(),
        create_get_project_router(),
        create_update_project_router(),
        create_archive_project_router(),
        create_delete_project_router(),
    ):
        router.include_router(sub_router)
    return router
