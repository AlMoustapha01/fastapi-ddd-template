"""Archive rule HTTP controller."""

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
    ArchiveRuleCommand,
    ArchiveRuleRequest,
    ArchiveRuleResponse,
    FlushError,
)
from modules.rules.domain.exceptions import (
    RuleNotFoundError,
    RuleValidationError,
)


class ArchiveRuleRequestPydantic(BaseModel):
    """Pydantic model for archiving a rule."""

    model_config = ConfigDict(frozen=True)

    reason: str | None = Field(None, description="Optional reason for archiving")


def create_archive_rule_router() -> APIRouter:
    """Create router for archive rule endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/{rule_id}/archive",
        description=getdoc(ArchiveRuleCommand),
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
        response_model=ArchiveRuleResponse,
    )
    @inject
    async def archive_rule(
        command: FromDishka[ArchiveRuleCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        request_data_pydantic: ArchiveRuleRequestPydantic,
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_rule_management"]))],
    ) -> ArchiveRuleResponse:
        """
        Archive a rule.

        Transitions the rule from IN_PRODUCTION to ARCHIVED status.
        """
        request_data = ArchiveRuleRequest(
            id=rule_id,
            archived_by=request.state.db_user.id_.value,
            reason=request_data_pydantic.reason,
        )
        return await command.execute(request_data)

    return router
