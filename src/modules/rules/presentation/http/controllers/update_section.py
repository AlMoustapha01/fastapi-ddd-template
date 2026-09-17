"""Update section name and description HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.rules.application.commands import (
    UpdateSectionCommand,
    UpdateSectionRequest,
    UpdateSectionResponse,
)
from modules.rules.domain.exceptions import SectionNotFoundError, SectionValidationError
from modules.rules.domain.exceptions.rule import RuleAlreadyExistsError


class UpdateSectionRequestPydantic(BaseModel):
    """Pydantic model for updating section name and description."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="Section name")
    description: str = Field(..., description="Section description")


def create_update_section_router() -> APIRouter:
    """Create router for update section details endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{section_id}/update",
        description=getdoc(UpdateSectionCommand),
        error_map={
            SectionNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            SectionValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            RuleAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=UpdateSectionResponse,
    )
    @inject
    async def update_section_details(
        command: FromDishka[UpdateSectionCommand],
        section_id: Annotated[UUID, Path(description="Section ID")],
        request_data_pydantic: UpdateSectionRequestPydantic,
        _: Annotated[AuthUser, Depends(require_roles(["perm_edit_section"]))],
    ) -> UpdateSectionResponse:
        """
        Update section name and description.

        Args:
            command: Injected UpdateSectionDetailsCommand
            section_id: UUID of the section to update
            request_data_pydantic: Data containing new name and description

        Returns:
            UpdateSectionDetailsResponse with updated section

        Raises:
            SectionNotFoundError: When section is not found
            SectionValidationError: When validation fails
        """
        request_data = UpdateSectionRequest(
            id=section_id,
            name=request_data_pydantic.name,
            description=request_data_pydantic.description,
        )
        return await command.execute(request_data)

    return router
