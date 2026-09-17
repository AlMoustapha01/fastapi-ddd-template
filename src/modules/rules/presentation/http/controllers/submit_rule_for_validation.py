"""Submit rule for validation HTTP controller."""

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
    SubmitRuleForValidationCommand,
    SubmitRuleForValidationRequest,
    SubmitRuleForValidationResponse,
)
from modules.rules.domain.exceptions import (
    RuleNotFoundError,
    RuleValidationError,
)


class SubmitRuleForValidationRequestPydantic(BaseModel):
    """Pydantic model for submitting rule for validation."""

    model_config = ConfigDict(frozen=True)

    reason: str | None = Field(None, description="Optional reason for submission")


def create_submit_rule_for_validation_router() -> APIRouter:
    """Create router for submit rule for validation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/{rule_id}/submit-for-validation",
        description=getdoc(SubmitRuleForValidationCommand),
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
        response_model=SubmitRuleForValidationResponse,
    )
    @inject
    async def submit_rule_for_validation(
        command: FromDishka[SubmitRuleForValidationCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        request_data_pydantic: SubmitRuleForValidationRequestPydantic,
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_edit_rule"]))],
    ) -> SubmitRuleForValidationResponse:
        """
        Submit a rule for validation.

        Transitions the rule from DRAFT to TO_VALIDATE status.
        """
        request_data = SubmitRuleForValidationRequest(
            id=rule_id,
            submitted_by=request.state.db_user.id_.value,
            reason=request_data_pydantic.reason,
        )
        return await command.execute(request_data)

    return router
