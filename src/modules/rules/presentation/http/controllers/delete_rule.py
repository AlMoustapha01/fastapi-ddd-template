"""Delete Rule HTTP controller."""

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
from modules.auth.domain.user import AuthUser
from modules.rules.application.commands import (
    DeleteRuleCommand,
    DeleteRuleRequest,
    FlushError,
)
from modules.rules.domain.exceptions import RuleInvalidStatusError, RuleNotFoundError


def create_delete_rule_router() -> APIRouter:
    """Create router for delete Rule endpoint."""
    router = ErrorAwareRouter()

    @router.delete(
        "/{rule_id}",
        description=getdoc(DeleteRuleCommand),
        error_map={
            RuleNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            RuleInvalidStatusError: rule(
                status=status.HTTP_400_BAD_REQUEST,
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
        status_code=status.HTTP_204_NO_CONTENT,
    )
    @inject
    async def delete_rule(
        command: FromDishka[DeleteRuleCommand],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_delete_rule"]))],
    ) -> None:
        """
        Delete a Rule by its ID.

        Args:
            command: Injected DeleteRuleCommand
            Rule_id: UUID of the Rule to delete

        Raises:
            RuleNotFoundError: When Rule is not found
        """
        request_data = DeleteRuleRequest(id=rule_id)
        await command.execute(request_data)

    return router
