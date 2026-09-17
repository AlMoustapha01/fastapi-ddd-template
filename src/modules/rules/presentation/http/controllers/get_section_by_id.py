"""Get section by ID HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.rules.application.queries import (
    GetSectionByIdQuery,
    GetSectionByIdRequest,
    SectionDetailResponse,
)
from modules.rules.domain.exceptions import SectionNotFoundError, SectionValidationError


def create_get_section_by_id_router() -> APIRouter:
    """Create router for get section by ID endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/{section_id}",
        description=getdoc(GetSectionByIdQuery),
        error_map={
            SectionNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
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
        response_model=SectionDetailResponse,
    )
    @inject
    async def get_section_by_id(
        query: FromDishka[GetSectionByIdQuery],
        section_id: Annotated[UUID, Path(description="Section ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_section"]))],
    ) -> SectionDetailResponse:
        """
        Get a section by its ID.

        Args:
            query: Injected GetSectionByIdQuery
            section_id: UUID of the section to retrieve

        Returns:
            SectionDetailResponse with section details

        Raises:
            SectionNotFoundError: When section is not found
            SectionValidationError: When validation fails
        """
        request_data = GetSectionByIdRequest(id=section_id)
        return await query.execute(request_data)

    return router
