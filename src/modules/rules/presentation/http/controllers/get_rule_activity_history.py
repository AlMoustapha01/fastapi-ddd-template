"""Get rule activity history HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Path, Query, status
from fastapi_error_map import ErrorAwareRouter, rule

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.rules.application.queries.get_rule_activity_history import (
    GetRuleActivityHistoryQuery,
    GetRuleActivityHistoryRequest,
    RuleActivityHistoryResponse,
)
from modules.rules.domain.exceptions import RuleNotFoundError


def create_get_rule_activity_history_router() -> APIRouter:
    """Create router for get rule activity history endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/{rule_id}/activity-history",
        description=getdoc(GetRuleActivityHistoryQuery),
        error_map={
            RuleNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=RuleActivityHistoryResponse,
    )
    @inject
    async def get_rule_activity_history(
        query: FromDishka[GetRuleActivityHistoryQuery],
        rule_id: Annotated[UUID, Path(description="Rule ID")],
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        limit: Annotated[
            int, Query(ge=1, le=100, description="Number of events per page")
        ] = 10,
    ) -> RuleActivityHistoryResponse:
        """
        Get the activity history of a rule.

        Returns a paginated list of all events that occurred on the rule,
        including who performed each action, when it happened, and what changed.
        """
        request_data = GetRuleActivityHistoryRequest(
            rule_id=rule_id,
            page=page,
            limit=limit,
        )
        return await query.execute(request_data)

    return router
