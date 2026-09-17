"""Archive rule command."""

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
class ArchiveRuleRequest:
    """Request to archive a rule."""

    id: UUID
    archived_by: UUID
    reason: str | None = None


class ArchiveRuleResponse(TypedDict):
    """Response for archived rule."""

    id: UUID
    status: str


class ArchiveRuleCommand:
    """Command to archive a rule."""

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

    async def execute(self, request: ArchiveRuleRequest) -> ArchiveRuleResponse:
        log.info("Archiving rule: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        # Archive rule (emits domain event)
        rule.archive(by_user=request.archived_by, reason=request.reason)

        # Save rule and audit events
        await self._rule_repository.save(rule)
        await self._audit_repository.save_many(rule.pop_events())
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            "Rule archived successfully: id=%s, status=%s",
            request.id,
            rule.props.status.value,
        )

        return ArchiveRuleResponse(
            id=rule.id_.value,
            status=rule.props.status.value,
        )
