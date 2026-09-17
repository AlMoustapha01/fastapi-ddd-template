"""Create section HTTP controller."""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Request, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.rules.application.commands import (
    CreateSectionCommand,
    CreateSectionRequest,
    CreateSectionResponse,
)
from modules.rules.domain.exceptions import (
    SectionAlreadyExistsError,
    SectionValidationError,
)


class CreateSectionRequestPydantic(BaseModel):
    """
    Pydantic model for create section request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="Section name")
    description: str = Field(..., description="Section description")


def create_create_section_router() -> APIRouter:
    """Create router for section creation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/",
        description=getdoc(CreateSectionCommand),
        error_map={
            SectionValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            SectionAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_201_CREATED,
        response_model=CreateSectionResponse,
    )
    @inject
    async def create_section(
        request_data_pydantic: CreateSectionRequestPydantic,
        command: FromDishka[CreateSectionCommand],
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_create_section"]))],
    ) -> CreateSectionResponse:
        """
        Create a new section.

        Args:
            request_data_pydantic: Section creation data
            command: Injected CreateSectionCommand

        Returns:
            CreateSectionResponse with the created section ID

        Raises:
            SectionAlreadyExistsError: When a section with the same slug exists
            SectionValidationError: When validation fails
            FlushError: When database operation fails
        """
        request_data = CreateSectionRequest(
            name=request_data_pydantic.name,
            description=request_data_pydantic.description,
            created_by_user_id=request.state.db_user.id_.value,
        )
        return await command.execute(request_data)

    return router
