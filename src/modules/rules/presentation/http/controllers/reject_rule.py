"""Reject rule HTTP controller."""

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
    FlushError,
    RejectRuleCommand,
    RejectRuleRequest,
    RejectRuleResponse,
)
from modules.rules.domain.exceptions import (
    RuleNotFoundError,
    RuleValidationError,
)


class RejectRuleRequestPydantic(BaseModel):
    """Pydantic model for rejecting a rule."""

    model_config = ConfigDict(frozen=True)

    reason: str = Field(
        ..., min_length=1, description="Reason for rejection (required)"
    )


def create_reject_rule_router() -> APIRouter:
    """Create router for reject rule endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/{rule_id}/reject",
        description=getdoc(RejectRuleCommand),
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
        response_model=RejectRuleResponse,
    )
    @inject
    async def reject_rule(
        command: FromDishka[RejectRuleCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        request_data_pydantic: RejectRuleRequestPydantic,
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_validate_rule"]))],
    ) -> RejectRuleResponse:
        """
        Reject a rule and send it back to draft.

        Transitions the rule from TO_VALIDATE to DRAFT status.
        A rejection reason is required.
        """
        request_data = RejectRuleRequest(
            id=rule_id,
            rejected_by=request.state.db_user.id_.value,
            reason=request_data_pydantic.reason,
        )
        return await command.execute(request_data)

    return router
