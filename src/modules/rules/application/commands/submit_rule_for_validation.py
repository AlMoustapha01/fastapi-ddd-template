"""Submit rule for validation command."""

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
class SubmitRuleForValidationRequest:
    """Request to submit a rule for validation."""

    id: UUID
    submitted_by: UUID
    reason: str | None = None


class SubmitRuleForValidationResponse(TypedDict):
    """Response for submitted rule."""

    id: UUID
    status: str


class SubmitRuleForValidationCommand:
    """Command to submit a rule for validation."""

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

    async def execute(
        self, request: SubmitRuleForValidationRequest
    ) -> SubmitRuleForValidationResponse:
        log.info("Submitting rule for validation: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        # Submit for validation (emits domain event)
        rule.submit_for_validation(by_user=request.submitted_by, reason=request.reason)

        # Save rule and audit events
        await self._rule_repository.save(rule)
        await self._audit_repository.save_many(rule.pop_events())
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            "Rule submitted for validation successfully: id=%s, status=%s",
            request.id,
            rule.props.status.value,
        )

        return SubmitRuleForValidationResponse(
            id=rule.id_.value,
            status=rule.props.status.value,
        )
