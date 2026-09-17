"""Approve rule command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.exceptions import RuleNotFoundError
from modules.rules.domain.ports import RuleAuditRepositoryPort, RuleRepositoryPort
from modules.rules.domain.value_objects import RuleId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ApproveRuleRequest:
    """Request to approve a rule."""

    id: UUID
    approved_by: UUID
    reason: str | None = None


class ApproveRuleResponse(TypedDict):
    """Response for approved rule."""

    id: UUID
    status: str


class ApproveRuleCommand:
    """Command to approve a rule and put it in production."""

    def __init__(
        self,
        rule_repository: RuleRepositoryPort,
        audit_repository: RuleAuditRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._rule_repository = rule_repository
        self._audit_repository = audit_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: ApproveRuleRequest) -> ApproveRuleResponse:
        log.info("Approving rule: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        # Approve rule (emits domain event)
        rule.approve(by_user=request.approved_by, reason=request.reason)

        # Save rule and audit events
        await self._rule_repository.save(rule)
        await self._audit_repository.save_many(rule.pop_events())
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            "Rule approved successfully: id=%s, status=%s",
            request.id,
            rule.props.status.value,
        )

        return ApproveRuleResponse(
            id=rule.id_.value,
            status=rule.props.status.value,
        )
