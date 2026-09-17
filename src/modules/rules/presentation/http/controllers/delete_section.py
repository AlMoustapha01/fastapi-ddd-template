"""Delete section HTTP controller."""

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
    DeleteSectionCommand,
    DeleteSectionRequest,
)
from modules.rules.domain.exceptions import SectionNotFoundError


def create_delete_section_router() -> APIRouter:
    """Create router for delete section endpoint."""
    router = ErrorAwareRouter()

    @router.delete(
        "/{section_id}",
        description=getdoc(DeleteSectionCommand),
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
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_section(
        command: FromDishka[DeleteSectionCommand],
        section_id: Annotated[UUID, Path(description="Section ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_delete_section"]))],
    ) -> None:
        """
        Delete a section by its ID.

        Args:
            command: Injected DeleteSectionCommand
            section_id: UUID of the section to delete

        Raises:
            SectionNotFoundError: When section is not found
        """
        request_data = DeleteSectionRequest(id=section_id)
        await command.execute(request_data)

    return router
