"""Authentication middleware."""

from fastapi import Depends
from fastapi.routing import APIRoute, APIRouter

from modules.auth.application.dependencies import get_current_user


def add_auth_to_routes(
    router: APIRouter, exclude_paths: list[str] | None = None
) -> None:
    """
    Add authentication to all routes in a router.

    Args:
        router: FastAPI router
        exclude_paths: List of paths to exclude from authentication

    Example:
        ```python
        router = APIRouter()
        # ... add routes ...
        add_auth_to_routes(router, exclude_paths=["/health", "/docs"])
        ```
    """
    exclude_paths = exclude_paths or []

    for route in router.routes:
        if isinstance(route, APIRoute):
            # Skip excluded paths
            if route.path in exclude_paths:
                continue

            # Add authentication dependency
            route.dependencies.append(Depends(get_current_user))
