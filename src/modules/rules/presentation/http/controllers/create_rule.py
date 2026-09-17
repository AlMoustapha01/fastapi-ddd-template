"""Create rule HTTP controller."""

from inspect import getdoc
from typing import Annotated, Any
from uuid import UUID

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
    CreateRuleCommand,
    CreateRuleRequest,
    CreateRuleResponse,
)
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import (
    RuleAlreadyExistsError,
    RuleValidationError,
)


class CreateRuleRequestPydantic(BaseModel):
    """
    Pydantic model for create rule request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    database_table_name: list[str] = Field(
        ..., min_length=1, description="List of database tables"
    )
    config: dict[str, Any] = Field(..., description="Rule configuration in JSON format")
    balance_type: BalanceType = Field(..., description="Balance type")
    profile_type: ProfileType = Field(..., description="Profile type")
    section_id: UUID = Field(..., description="Section ID")


def create_create_rule_router() -> APIRouter:
    """Create router for rule creation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/",
        description=getdoc(CreateRuleCommand),
        error_map={
            RuleValidationError: rule(
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
        status_code=status.HTTP_201_CREATED,
        response_model=CreateRuleResponse,
    )
    @inject
    async def create_rule(
        request_data_pydantic: CreateRuleRequestPydantic,
        command: FromDishka[CreateRuleCommand],
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_create_rule"]))],
    ) -> CreateRuleResponse:
        """
        Create a new rule.

        Args:
            request_data_pydantic: Rule creation data
            command: Injected CreateRuleCommand

        Returns:
            CreateRuleResponse with the created rule ID

        Raises:
            RuleAlreadyExistsError: When a rule with the same slug exists
            RuleValidationError: When validation fails
            FlushError: When database operation fails
        """
        request_data = CreateRuleRequest(
            name=request_data_pydantic.name,
            database_table_name=request_data_pydantic.database_table_name,
            config=request_data_pydantic.config,
            balance_type=request_data_pydantic.balance_type,
            profile_type=request_data_pydantic.profile_type,
            section_id=request_data_pydantic.section_id,
            created_by=request.state.db_user.id_.value,
        )
        return await command.execute(request_data)

    return router
