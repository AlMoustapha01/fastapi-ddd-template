"""Delete Rule command."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.enums import RuleStatus
from modules.rules.domain.exceptions import RuleInvalidStatusError, RuleNotFoundError
from modules.rules.domain.ports import RuleRepositoryPort
from modules.rules.domain.value_objects import RuleId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteRuleRequest:
    """Request to delete a Rule."""

    id: UUID


class DeleteRuleCommand:
    """Command to delete a Rule."""

    def __init__(
        self,
        rule_repository: RuleRepositoryPort,
        transaction_manager: TransactionManager,
    ) -> None:
        self._rule_repository = rule_repository
        self._transaction_manager = transaction_manager

    async def execute(self, request: DeleteRuleRequest) -> None:
        """
        Execute the delete Rule command.

        :param request: The Rule deletion request
        :raises RuleNotFoundError: When Rule is not found
        """
        log.info("Deleting Rule: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        if rule.props.status != RuleStatus.DRAFT:
            raise RuleInvalidStatusError(
                rule_id=str(request.id),
                current_status=rule.props.status.value,
                allowed_statuses=[RuleStatus.DRAFT.value],
                operation="delete",
            )

        await self._rule_repository.delete(rule)

        await self._transaction_manager.commit()

        log.info("Rule deleted successfully: %s", request.id)
