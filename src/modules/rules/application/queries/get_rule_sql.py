"""Get rule SQL representation query."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.enums.balance_type import BalanceType
from modules.rules.domain.enums.profile_type import ProfileType
from modules.rules.domain.enums.rule_status import RuleStatus
from modules.rules.domain.exceptions import RuleNotFoundError
from modules.rules.domain.ports import RuleRepositoryPort
from modules.rules.domain.value_objects import RuleId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRuleSqlRequest:
    """Request to get a rule's SQL representation."""

    id: UUID


class RuleSqlResponse(TypedDict):
    """Rule SQL representation response."""

    id: UUID
    name: str
    balance_type: BalanceType
    profile_type: ProfileType
    slug: str
    status: RuleStatus
    sql: str


class GetRuleSqlQuery:
    """Query to get a rule's SQL representation."""

    def __init__(self, rule_repository: RuleRepositoryPort) -> None:
        self._rule_repository = rule_repository

    async def execute(self, request: GetRuleSqlRequest) -> RuleSqlResponse:
        """
        Execute the get rule SQL query.

        :param request: The request with rule ID
        :return: Rule SQL representation
        :raises RuleNotFoundError: When rule is not found
        """
        log.info("Fetching rule SQL by ID: %s", request.id)

        # Create RuleId value object
        rule_id = RuleId(request.id)

        # Fetch rule from repository
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        log.info("Generating SQL for rule: %s", rule.id_.value)

        # Generate SQL from config
        sql = rule.props.config.to_sql()

        # Map to response
        return RuleSqlResponse(
            id=rule.id_.value,
            name=rule.props.name,
            balance_type=rule.props.balance_type,
            profile_type=rule.props.profile_type,
            slug=rule.props.slug.value,
            status=rule.props.status,
            sql=sql,
        )
