"""Reject rule command."""

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
class RejectRuleRequest:
    """Request to reject a rule."""

    id: UUID
    rejected_by: UUID
    reason: str


class RejectRuleResponse(TypedDict):
    """Response for rejected rule."""

    id: UUID
    status: str


class RejectRuleCommand:
    """Command to reject a rule and send it back to draft."""

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

    async def execute(self, request: RejectRuleRequest) -> RejectRuleResponse:
        log.info("Rejecting rule: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        # Reject rule (emits domain event)
        rule.reject(by_user=request.rejected_by, reason=request.reason)

        # Save rule and audit events
        await self._rule_repository.save(rule)
        await self._audit_repository.save_many(rule.pop_events())
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            "Rule rejected successfully: id=%s, status=%s, reason=%s",
            request.id,
            rule.props.status.value,
            request.reason,
        )

        return RejectRuleResponse(
            id=rule.id_.value,
            status=rule.props.status.value,
        )
