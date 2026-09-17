"""Dishka provider for rules module."""

from dishka import Provider, Scope, provide, provide_all

from core.lib.db.main_transaction_manager_sqla import SqlaMainTransactionManager
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.application.commands import (
    ApproveRuleCommand,
    ArchiveRuleCommand,
    BulkCreateRulesCommand,
    BulkCreateSectionsCommand,
    CreateRuleCommand,
    CreateSectionCommand,
    DeleteRuleCommand,
    DeleteSectionCommand,
    MakeActiveSectionCommand,
    MakeInactiveSectionCommand,
    RejectRuleCommand,
    SqlaRuleFlusher,
    SqlaSectionFlusher,
    SubmitRuleForValidationCommand,
    UpdateRuleCommand,
    UpdateSectionCommand,
)
from modules.rules.application.queries import (
    GetRuleActivityHistoryQuery,
    GetRuleByIdQuery,
    GetRuleBySlugQuery,
    GetRuleSqlQuery,
    GetRulesQuery,
    GetSectionByIdQuery,
    GetSectionBySlugQuery,
    GetSectionsQuery,
)
from modules.rules.domain.ports import (
    RuleAuditRepositoryPort,
    RuleRepositoryPort,
    SectionRepositoryPort,
)
from modules.rules.infrastructure.mappers import RuleMapper, SectionMapper
from modules.rules.infrastructure.repositories import (
    RuleAuditRepository,
    RuleRepository,
    SectionRepository,
)


class RulesProvider(Provider):
    """Provider for rules module dependencies."""

    scope = Scope.REQUEST

    # Mappers
    mappers = provide_all(
        SectionMapper,
        RuleMapper,
    )

    tx_manager = provide(SqlaMainTransactionManager, provides=TransactionManager)
    section_flusher = provide(SqlaSectionFlusher)
    rule_flusher = provide(SqlaRuleFlusher)

    # Repositories
    section_repository = provide(SectionRepository, provides=SectionRepositoryPort)
    rule_repository = provide(RuleRepository, provides=RuleRepositoryPort)
    rule_audit_repository = provide(
        RuleAuditRepository, provides=RuleAuditRepositoryPort
    )
    # Commands
    commands = provide_all(
        ApproveRuleCommand,
        ArchiveRuleCommand,
        BulkCreateRulesCommand,
        BulkCreateSectionsCommand,
        CreateRuleCommand,
        CreateSectionCommand,
        DeleteRuleCommand,
        DeleteSectionCommand,
        MakeActiveSectionCommand,
        MakeInactiveSectionCommand,
        RejectRuleCommand,
        SubmitRuleForValidationCommand,
        UpdateRuleCommand,
        UpdateSectionCommand,
    )

    # Queries
    queries = provide_all(
        GetRuleActivityHistoryQuery,
        GetRuleByIdQuery,
        GetRuleBySlugQuery,
        GetRuleSqlQuery,
        GetRulesQuery,
        GetSectionByIdQuery,
        GetSectionsQuery,
        GetSectionBySlugQuery,
    )
