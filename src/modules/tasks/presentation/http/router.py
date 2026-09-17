"""HTTP router of the tasks module."""

from fastapi import APIRouter

from modules.tasks.presentation.http.controllers import (
    create_change_task_status_router,
    create_create_task_router,
    create_delete_task_router,
    create_get_task_router,
    create_list_tasks_router,
    create_update_task_router,
)


def create_tasks_router() -> APIRouter:
    router = APIRouter(tags=["Tasks"])
    for sub_router in (
        create_create_task_router(),
        create_list_tasks_router(),
        create_get_task_router(),
        create_update_task_router(),
        create_change_task_status_router(),
        create_delete_task_router(),
    ):
        router.include_router(sub_router)
    return router
