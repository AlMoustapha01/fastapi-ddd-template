"""Get rule by slug HTTP controller."""

from inspect import getdoc
from typing import Annotated

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
    GetRuleBySlugQuery,
    GetRuleBySlugRequest,
    RuleDetailResponse,
)
from modules.rules.domain.exceptions import RuleNotFoundError, RuleValidationError


def create_get_rule_by_slug_router() -> APIRouter:
    """Create router for get rule by slug endpoint."""
    router = ErrorAwareRouter()

    @router.get(
        "/by-slug/{slug}",
        description=getdoc(GetRuleBySlugQuery),
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
        response_model=RuleDetailResponse,
    )
    @inject
    async def get_rule_by_slug(
        query: FromDishka[GetRuleBySlugQuery],
        slug: Annotated[str, Path(description="Rule slug")],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_rule"]))],
    ) -> RuleDetailResponse:
        """
        Get a rule by its slug.

        Args:
            query: Injected GetRuleBySlugQuery
            slug: Slug of the rule to retrieve

        Returns:
            RuleDetailResponse with rule details

        Raises:
            RuleNotFoundError: When rule is not found
            RuleValidationError: When validation fails
        """
        request_data = GetRuleBySlugRequest(slug=slug)
        return await query.execute(request_data)

    return router
