"""Get rule by slug query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID

from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.exceptions import RuleNotFoundError
from modules.rules.domain.ports import RuleRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRuleBySlugRequest:
    """Request to get a rule by slug."""

    slug: str


class RuleDetailResponse(TypedDict):
    """Detailed rule response data."""

    id: UUID
    name: str
    slug: str
    profile_type: str
    balance_type: str
    section_id: UUID
    config: dict[str, Any]
    database_table_name: list[str]
    status: str
    created_at: datetime
    updated_at: datetime


class GetRuleBySlugQuery:
    """Query to get a rule by its slug."""

    def __init__(self, rule_repository: RuleRepositoryPort) -> None:
        self._rule_repository = rule_repository

    async def execute(self, request: GetRuleBySlugRequest) -> RuleDetailResponse:
        """
        Execute the get rule by slug query.

        :param request: The request with rule slug
        :return: Detailed rule response
        :raises RuleNotFoundError: When rule is not found
        """
        log.info("Fetching rule by slug: %s", request.slug)

        # Fetch rule from repository
        rule: Rule | None = await self._rule_repository.find_one_by_slug(request.slug)

        if rule is None:
            log.warning("Rule not found with slug: %s", request.slug)
            raise RuleNotFoundError(request.slug)

        log.info("Rule found: %s", rule.id_.value)

        # Map to response
        return RuleDetailResponse(
            id=rule.id_.value,
            name=rule.props.name,
            slug=rule.props.slug.value,
            profile_type=rule.props.profile_type.value,
            balance_type=rule.props.balance_type.value,
            section_id=rule.props.section_id.value,
            config=rule.props.config.to_dict(),
            database_table_name=rule.props.database_table_name,
            status=rule.props.status.value,
            created_at=rule.created_at_,
            updated_at=rule.updated_at_,
        )
