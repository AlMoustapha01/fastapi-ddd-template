"""Get sections HTTP controller."""

from datetime import datetime
from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.db.repository.paginated import SortOrder
from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.rules.application.queries import (
    GetSectionsQuery,
    GetSectionsRequest,
    GetSectionsResponse,
)
from modules.rules.domain.enums import SectionStatus
from modules.rules.domain.exceptions import SectionValidationError


def create_get_sections_router() -> APIRouter:
    """Create router for get sections endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/",
        description=getdoc(GetSectionsQuery),
        error_map={
            SectionValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=GetSectionsResponse,
    )
    @inject
    async def get_sections(
        query: FromDishka[GetSectionsQuery],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_section"]))],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 10,
        order_by_field: Annotated[
            str | None,
            Query(description="Field to order by (e.g., 'name', 'created_at')"),
        ] = None,
        order_by_direction: Annotated[
            SortOrder, Query(description="Sort direction (ASC or DESC)")
        ] = SortOrder.ASC,
        status_filter: Annotated[
            SectionStatus | None,
            Query(alias="status", description="Filter by status (ACTIVE or INACTIVE)"),
        ] = None,
        search: Annotated[
            str | None,
            Query(description="Search in name and slug"),
        ] = None,
        start_created_at: Annotated[
            datetime | None,
            Query(description="Filter sections created after this date"),
        ] = None,
        end_created_at: Annotated[
            datetime | None,
            Query(description="Filter sections created before this date"),
        ] = None,
    ) -> GetSectionsResponse:
        """
        Get all sections with pagination.

        Args:
            query: Injected GetSectionsQuery
            page: Page number (starts at 1)
            limit: Number of items per page (max 100)
            order_by_field: Field to order by
            order_by_direction: Sort direction
            status_filter: Filter by section status
            search: Search term for name/slug
            start_created_at: Filter by creation date (from)
            end_created_at: Filter by creation date (to)

        Returns:
            GetSectionsResponse with paginated sections

        Raises:
            SectionValidationError: When validation fails
        """
        request_data = GetSectionsRequest(
            page=page,
            limit=limit,
            order_by_field=order_by_field,
            order_by_direction=order_by_direction,
            status=status_filter,
            search=search,
            start_created_at=start_created_at,
            end_created_at=end_created_at,
        )
        return await query.execute(request_data)

    return router
