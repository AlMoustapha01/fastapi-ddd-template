"""Update rule HTTP controller."""

from inspect import getdoc
from typing import Annotated, Any
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, Request, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.rules.application.commands import (
    FlushError,
    UpdateRuleCommand,
    UpdateRuleRequest,
    UpdateRuleResponse,
)
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import (
    RuleAlreadyExistsError,
    RuleInvalidStatusError,
    RuleNotFoundError,
    RuleValidationError,
)


class UpdateRuleRequestPydantic(BaseModel):
    """Pydantic model for updating rule details."""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(
        None, min_length=1, max_length=255, description="Rule name"
    )
    database_table_name: list[str] | None = Field(
        None, description="List of related database table names"
    )
    config: dict[str, Any] | None = Field(
        None, description="Configuration parameters of the rule"
    )
    balance_type: BalanceType | None = Field(
        None, description="Type of balance associated with the rule"
    )
    profile_type: ProfileType | None = Field(
        None, description="Type of profile associated with the rule"
    )
    section_id: UUID | None = Field(None, description="Linked section ID")


def create_update_rule_router() -> APIRouter:
    """Create router for update rule details endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{rule_id}",
        description=getdoc(UpdateRuleCommand),
        error_map={
            RuleNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            RuleValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            RuleInvalidStatusError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            RuleAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            FlushError: rule(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=UpdateRuleResponse,
    )
    @inject
    async def update_rule_details(
        command: FromDishka[UpdateRuleCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        request_data_pydantic: UpdateRuleRequestPydantic,
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_edit_rule"]))],
    ) -> UpdateRuleResponse:
        """
        Update rule details (name, config, section, status, etc.).
        """
        request_data = UpdateRuleRequest(
            id=rule_id,
            name=request_data_pydantic.name,
            database_table_name=request_data_pydantic.database_table_name,
            balance_type=request_data_pydantic.balance_type,
            profile_type=request_data_pydantic.profile_type,
            config=request_data_pydantic.config,
            section_id=request_data_pydantic.section_id,
            updated_by=request.state.db_user.id_.value,
        )
        return await command.execute(request_data)

    return router
