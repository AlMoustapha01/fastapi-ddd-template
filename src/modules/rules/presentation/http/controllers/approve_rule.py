"""Approve rule HTTP controller."""

from inspect import getdoc
from typing import Annotated
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
    ApproveRuleCommand,
    ApproveRuleRequest,
    ApproveRuleResponse,
    FlushError,
)
from modules.rules.domain.exceptions import (
    RuleNotFoundError,
    RuleValidationError,
)


class ApproveRuleRequestPydantic(BaseModel):
    """Pydantic model for approving a rule."""

    model_config = ConfigDict(frozen=True)

    reason: str | None = Field(None, description="Optional reason for approval")


def create_approve_rule_router() -> APIRouter:
    """Create router for approve rule endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/{rule_id}/approve",
        description=getdoc(ApproveRuleCommand),
        error_map={
            RuleNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            RuleValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            FlushError: rule(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                translator=DomainErrorTranslator(),
            ),
            ValueError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=ApproveRuleResponse,
    )
    @inject
    async def approve_rule(
        command: FromDishka[ApproveRuleCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        request_data_pydantic: ApproveRuleRequestPydantic,
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_validate_rule"]))],
    ) -> ApproveRuleResponse:
        """
        Approve a rule and put it in production.

        Transitions the rule from TO_VALIDATE to IN_PRODUCTION status.
        """
        request_data = ApproveRuleRequest(
            id=rule_id,
            approved_by=request.state.db_user.id_.value,
            reason=request_data_pydantic.reason,
        )
        return await command.execute(request_data)

    return router
