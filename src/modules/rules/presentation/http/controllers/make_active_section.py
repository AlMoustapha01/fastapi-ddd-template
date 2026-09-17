"""Make section active HTTP controller."""

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
    MakeActiveSectionCommand,
    MakeActiveSectionRequest,
    MakeActiveSectionResponse,
)
from modules.rules.domain.exceptions import SectionNotFoundError


def create_make_active_section_router() -> APIRouter:
    """Create router for activate section endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{section_id}/activate",
        description=getdoc(MakeActiveSectionCommand),
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
        response_model=MakeActiveSectionResponse,
    )
    @inject
    async def make_section_active(
        command: FromDishka[MakeActiveSectionCommand],
        section_id: Annotated[UUID, Path(description="Section ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_activate_section"]))],
    ) -> MakeActiveSectionResponse:
        """
        Activate a section.
        """
        request_data = MakeActiveSectionRequest(id=section_id)
        return await command.execute(request_data)

    return router
