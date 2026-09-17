"""Update rule details command."""

import logging
from dataclasses import dataclass
from typing import Any, TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import RuleNotFoundError
from modules.rules.domain.ports import RuleAuditRepositoryPort, RuleRepositoryPort
from modules.rules.domain.value_objects import RuleId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateRuleRequest:
    """Request to update Rule details."""

    id: UUID
    name: str | None = None
    database_table_name: list[str] | None = None
    config: dict[str, Any] | None = None
    balance_type: BalanceType | None = None
    profile_type: ProfileType | None = None
    section_id: UUID | None = None
    updated_by: UUID


class UpdateRuleResponse(TypedDict):
    """Response for updated Rule details."""

    id: UUID


class UpdateRuleCommand:
    """Command to update rule details."""

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

    async def execute(self, request: UpdateRuleRequest) -> UpdateRuleResponse:
        log.info("Updating rule: %s", request.id)

        rule_id = RuleId(request.id)
        rule: Rule | None = await self._rule_repository.find_one_by_id(rule_id)

        if rule is None:
            log.warning("Rule not found: %s", request.id)
            raise RuleNotFoundError(str(request.id))

        self._update_rule_fields(rule, request)

        await self._rule_repository.save(rule)
        await self._audit_repository.save_many(rule.pop_events())

        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            f"Rule updated successfully: id={request.id}, "
            f"name={rule.props.name}, "
            f"slug={rule.props.slug.value}, "
        )

        return UpdateRuleResponse(id=rule.id_.value)

    def _update_rule_fields(self, rule: Rule, request: UpdateRuleRequest) -> None:
        if request.name is not None:
            rule.update_name(request.name, request.updated_by, None)

        if request.database_table_name is not None:
            rule.update_database_table_name(
                request.database_table_name, request.updated_by
            )

        if request.balance_type is not None:
            rule.update_balance_type(request.balance_type, request.updated_by)

        if request.profile_type is not None:
            rule.update_profile_type(request.profile_type, request.updated_by)

        if request.section_id is not None:
            rule.update_section_id(request.section_id, request.updated_by)

        if request.config is not None:
            rule.update_config(request.config, request.updated_by, None)
