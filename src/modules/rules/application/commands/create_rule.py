"""Create rule command."""

import logging
from dataclasses import dataclass
from typing import Any, TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.rule import CreateRuleProps, Rule
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import RuleAlreadyExistsError
from modules.rules.domain.ports import RuleAuditRepositoryPort, RuleRepositoryPort
from modules.rules.domain.value_objects import RuleConfig, SectionId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRuleRequest:
    name: str
    database_table_name: list[str]
    config: dict[str, Any]  # Will be converted to RuleConfig
    balance_type: BalanceType
    profile_type: ProfileType
    section_id: UUID
    created_by: UUID


class CreateRuleResponse(TypedDict):
    id: UUID


class CreateRuleCommand:
    """Command to create a new rule."""

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

    async def execute(self, request: CreateRuleRequest) -> CreateRuleResponse:
        """
        Execute the create rule command.

        :param request: The rule creation request
        :return: Response with the created rule ID
        :raises RuleAlreadyExistsError: When a rule with the same slug exists
        """
        log.info("Creating rule: %s", request.name)

        rule_config = RuleConfig.from_dict(request.config)

        rule = Rule.create(
            props=CreateRuleProps(
                name=request.name,
                database_table_name=request.database_table_name,
                config=rule_config,
                balance_type=request.balance_type,
                profile_type=request.profile_type,
                section_id=SectionId(request.section_id),
                created_by=request.created_by,
            )
        )

        # Save rule and audit events
        await self._rule_repository.add(rule)
        await self._audit_repository.save_many(rule.pop_events())

        try:
            await self._flusher.flush()
        except RuleAlreadyExistsError:
            log.warning("Rule already exists with slug: %s", rule.props.slug.value)
            raise

        await self._transaction_manager.commit()

        log.info("Rule created successfully: %s", rule.id_.value)

        return CreateRuleResponse(id=rule.id_.value)
