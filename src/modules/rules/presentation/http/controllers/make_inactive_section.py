"""Make section inactive HTTP controller."""

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
from modules.rules.application.commands import (
    MakeInactiveSectionCommand,
    MakeInactiveSectionRequest,
    MakeInactiveSectionResponse,
)
from modules.rules.domain.exceptions import SectionNotFoundError


def create_make_inactive_section_router() -> APIRouter:
    """Create router for deactivate section endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{section_id}/deactivate",
        description=getdoc(MakeInactiveSectionCommand),
        error_map={
            SectionNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=MakeInactiveSectionResponse,
    )
    @inject
    async def make_section_inactive(
        command: FromDishka[MakeInactiveSectionCommand],
        section_id: Annotated[UUID, Path(description="Section ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_deactivate_section"]))],
    ) -> MakeInactiveSectionResponse:
        """
        Deactivate a section.
        """
        request_data = MakeInactiveSectionRequest(id=section_id)
        return await command.execute(request_data)

    return router
