"""Bulk create rules command."""

import logging
from dataclasses import dataclass
from typing import Any, TypedDict
from uuid import UUID

from core.lib.db.transaction_manager import TransactionManager
from modules.rules.application.commands.create_rule_flusher_sqla import SqlaRuleFlusher
from modules.rules.domain.entities.rule import CreateRuleProps, Rule
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.ports import RuleAuditRepositoryPort, RuleRepositoryPort
from modules.rules.domain.value_objects import RuleConfig, SectionId, SlugValueObject

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkCreateRuleItem:
    """Single rule item for bulk creation."""

    name: str
    database_table_name: list[str]
    config: dict[str, Any]
    balance_type: BalanceType
    profile_type: ProfileType
    section_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkCreateRulesRequest:
    """Request to create multiple rules."""

    rules: list[BulkCreateRuleItem]
    created_by: UUID


class BulkCreateRuleResult(TypedDict):
    """Result for a single rule creation."""

    id: UUID
    name: str
    slug: str


class BulkCreateRulesResponse(TypedDict):
    """Response for bulk rule creation."""

    created: list[BulkCreateRuleResult]
    skipped: list[str]
    total_created: int
    total_skipped: int


class BulkCreateRulesCommand:
    """Command to create multiple rules at once."""

    def __init__(
        self,
        rule_repository: RuleRepositoryPort,
        audit_repository: RuleAuditRepositoryPort,
        rule_flusher: SqlaRuleFlusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._rule_repository = rule_repository
        self._audit_repository = audit_repository
        self._flusher = rule_flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: BulkCreateRulesRequest) -> BulkCreateRulesResponse:
        """
        Execute the bulk create rules command.

        Skips rules that already exist (based on slug).

        :param request: The bulk rule creation request
        :return: Response with created and skipped rules
        """
        log.info("Creating %d rules in bulk", len(request.rules))

        created_rules: list[Rule] = []
        skipped_slugs: list[str] = []

        for rule_item in request.rules:
            # Generate slug to check if rule already exists
            slug = SlugValueObject.from_text(rule_item.name)
            existing = await self._rule_repository.find_one_by_slug(slug.value)

            if existing:
                log.debug("Skipping existing rule with slug: %s", slug.value)
                skipped_slugs.append(slug.value)
                continue

            rule_config = RuleConfig.from_dict(rule_item.config)

            rule = Rule.create(
                props=CreateRuleProps(
                    name=rule_item.name,
                    database_table_name=rule_item.database_table_name,
                    config=rule_config,
                    balance_type=rule_item.balance_type,
                    profile_type=rule_item.profile_type,
                    section_id=SectionId(rule_item.section_id),
                    created_by=request.created_by,
                )
            )
            await self._rule_repository.add(rule)
            await self._audit_repository.save_many(rule.pop_events())
            created_rules.append(rule)

        if created_rules:
            await self._flusher.flush()
            await self._transaction_manager.commit()

        log.info(
            "Bulk create rules completed: %d created, %d skipped",
            len(created_rules),
            len(skipped_slugs),
        )

        return BulkCreateRulesResponse(
            created=[
                BulkCreateRuleResult(
                    id=rule.id_.value,
                    name=rule.props.name,
                    slug=rule.props.slug.value,
                )
                for rule in created_rules
            ],
            skipped=skipped_slugs,
            total_created=len(created_rules),
            total_skipped=len(skipped_slugs),
        )
