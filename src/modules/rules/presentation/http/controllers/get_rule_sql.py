"""Get rule SQL representation HTTP controller."""

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
from modules.rules.application.queries import (
    GetRuleSqlQuery,
    GetRuleSqlRequest,
    RuleSqlResponse,
)
from modules.rules.domain.exceptions import RuleNotFoundError, RuleValidationError


def create_get_rule_sql_router() -> APIRouter:
    """Create router for get rule SQL endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/{rule_id}/sql",
        description=getdoc(GetRuleSqlQuery),
        error_map={
            RuleNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            RuleValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=RuleSqlResponse,
    )
    @inject
    async def get_rule_sql(
        query: FromDishka[GetRuleSqlQuery],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_rule"]))],
    ) -> RuleSqlResponse:
        """
        Get SQL representation of a rule.

        Args:
            query: Injected GetRuleSqlQuery
            rule_id: UUID of the rule

        Returns:
            RuleSqlResponse with SQL representation

        Raises:
            RuleNotFoundError: When rule is not found
            RuleValidationError: When validation fails
        """
        request_data = GetRuleSqlRequest(id=rule_id)
        return await query.execute(request_data)

    return router
