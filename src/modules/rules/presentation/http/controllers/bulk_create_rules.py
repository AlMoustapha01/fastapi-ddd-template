"""Bulk create rules HTTP controller."""

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
    BulkCreateRuleItem,
    BulkCreateRulesCommand,
    BulkCreateRulesRequest,
    BulkCreateRulesResponse,
)
from modules.rules.application.commands.create_rule_flusher_sqla import FlushError
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import (
    RuleAlreadyExistsError,
    RuleValidationError,
)


class RuleItemPydantic(BaseModel):
    """Pydantic model for a single rule item."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="Rule name")
    database_table_name: list[str] = Field(..., description="Database table names")
    config: dict[str, Any] = Field(..., description="Rule configuration")
    balance_type: BalanceType = Field(..., description="Balance type")
    profile_type: ProfileType = Field(..., description="Profile type")
    section_id: str = Field(..., description="Section ID (UUID)")


class BulkCreateRulesRequestPydantic(BaseModel):
    """
    Pydantic model for bulk create rules request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    rules: list[RuleItemPydantic] = Field(
        ..., min_length=1, description="List of rules to create"
    )


def create_bulk_create_rules_router() -> APIRouter:
    """Create router for bulk rule creation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/bulk",
        description=getdoc(BulkCreateRulesCommand),
        error_map={
            RuleValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            RuleAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            FlushError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_201_CREATED,
        response_model=BulkCreateRulesResponse,
    )
    @inject
    async def bulk_create_rules(
        request_data_pydantic: BulkCreateRulesRequestPydantic,
        command: FromDishka[BulkCreateRulesCommand],
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_create_rule"]))],
    ) -> BulkCreateRulesResponse:
        """
        Create multiple rules at once.

        Args:
            request_data_pydantic: Bulk rule creation data
            command: Injected BulkCreateRulesCommand

        Returns:
            BulkCreateRulesResponse with the created rules

        Raises:
            RuleAlreadyExistsError: When a rule with the same slug exists
            RuleValidationError: When validation fails
            FlushError: When database operation fails
        """
        request_data = BulkCreateRulesRequest(
            rules=[
                BulkCreateRuleItem(
                    name=rule_item.name,
                    database_table_name=rule_item.database_table_name,
                    config=rule_item.config,
                    balance_type=rule_item.balance_type,
                    profile_type=rule_item.profile_type,
                    section_id=UUID(rule_item.section_id),
                )
                for rule_item in request_data_pydantic.rules
            ],
            created_by=request.state.db_user.id_.value,
        )
        return await command.execute(request_data)

    return router
