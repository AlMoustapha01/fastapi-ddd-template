"""Get rules query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID

from core.lib.db.repository.paginated import (
    FilterBy,
    FilterGroup,
    Operator,
    OrderBy,
    Paginated,
    PaginatedQueryParams,
    SortOrder,
)
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.domain.ports import RuleRepositoryPort

log = logging.getLogger(__name__)


# Statuts visibles par tous
PUBLIC_STATUSES = [
    RuleStatus.IN_PRODUCTION.value,
    RuleStatus.TO_VALIDATE.value,
    RuleStatus.ARCHIVED.value,
]


@dataclass(frozen=True, slots=True, kw_only=True)
class GetRulesRequest:
    """Request to get rules with pagination."""

    page: int = 1
    limit: int = 10
    order_by_field: str | None = None
    order_by_direction: SortOrder = SortOrder.ASC
    profile_type: ProfileType | None = None
    balance_type: BalanceType | None = None
    status: RuleStatus | None = None
    search: str | None = None
    current_user_id: UUID | None = None


class RuleResponse(TypedDict):
    """Rule response data."""

    id: UUID
    name: str
    slug: str
    profile_type: str
    balance_type: str
    section_id: UUID
    config: dict[str, Any]
    database_table_name: list[str]
    status: str
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class GetRulesResponse(TypedDict):
    """Paginated rules response."""

    count: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    data: list[RuleResponse]


class GetRulesQuery:
    """Query to get all rules with pagination."""

    def __init__(self, rule_repository: RuleRepositoryPort) -> None:
        self._rule_repository = rule_repository

    async def execute(self, request: GetRulesRequest) -> GetRulesResponse:
        """Execute the get rules query."""
        log.info(
            "Fetching rules: page=%d, limit=%d, profile_type=%s, balance_type=%s, "
            "status=%s, search=%s, current_user_id=%s",
            request.page,
            request.limit,
            request.profile_type,
            request.balance_type,
            request.status,
            request.search,
            request.current_user_id,
        )

        order_by = None
        if request.order_by_field:
            order_by = OrderBy[Rule](
                field=request.order_by_field,
                param=request.order_by_direction,
            )

        filters: list[FilterBy[Rule]] = []
        filter_groups: list[FilterGroup[Rule]] = []

        # Filtres de base
        if request.profile_type:
            filters.append(
                FilterBy[Rule](
                    field="profile_type",
                    operator=Operator.EQ,
                    value=request.profile_type.value,
                )
            )
        if request.balance_type:
            filters.append(
                FilterBy[Rule](
                    field="balance_type",
                    operator=Operator.EQ,
                    value=request.balance_type.value,
                )
            )

        # Gestion des statuts
        status_filter = self._build_status_filter(
            requested_status=request.status,
            current_user_id=request.current_user_id,
        )
        if status_filter:
            filter_groups.append(status_filter)

        # Recherche sur name et slug
        if request.search:
            search_filters = [
                FilterBy[Rule](
                    field="name",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
                FilterBy[Rule](
                    field="slug",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
            ]
            filter_groups.append(FilterGroup[Rule](filters=search_filters, use_or=True))

        params = PaginatedQueryParams[Rule](
            page=request.page,
            limit=request.limit,
            order_by=order_by,
            filter_by=filters if filters else None,
            filter_groups=filter_groups if filter_groups else None,
        )

        paginated: Paginated[Rule] = await self._rule_repository.find_all_paginated(
            params
        )

        log.info(
            "Fetched %d rules (page %d/%d)",
            len(paginated.data),
            paginated.page,
            paginated.total_pages,
        )

        rules_data: list[RuleResponse] = [
            RuleResponse(
                id=rule.id_.value,
                name=rule.props.name,
                slug=rule.props.slug.value,
                profile_type=rule.props.profile_type.value,
                balance_type=rule.props.balance_type.value,
                section_id=rule.props.section_id.value,
                database_table_name=rule.props.database_table_name,
                config=rule.props.config.to_dict(),
                status=rule.props.status.value,
                created_by_user_id=rule.props.created_by.value,
                created_at=rule.created_at_,
                updated_at=rule.updated_at_,
            )
            for rule in paginated.data
        ]

        return GetRulesResponse(
            count=paginated.count,
            limit=paginated.limit,
            page=paginated.page,
            total_pages=paginated.total_pages,
            has_next=paginated.has_next,
            has_previous=paginated.has_previous,
            data=rules_data,
        )

    def _build_status_filter(
        self,
        requested_status: RuleStatus | None,
        current_user_id: UUID | None,
    ) -> FilterGroup[Rule] | None:
        """
        Build status filter based on visibility rules.

        Rules:
        - IN_PRODUCTION, TO_VALIDATE, ARCHIVED: visible by all
        - DRAFT: visible only by the creator

        If a specific status is requested, apply it with visibility constraints.
        If no status is requested, apply default visibility logic.
        """
        if requested_status:
            return self._build_specific_status_filter(requested_status, current_user_id)
        return self._build_default_status_filter(current_user_id)

    def _build_specific_status_filter(
        self,
        status: RuleStatus,
        current_user_id: UUID | None,
    ) -> FilterGroup[Rule] | None:
        """Build filter for a specific requested status."""
        if status == RuleStatus.DRAFT:
            # DRAFT visible uniquement par le créateur
            if not current_user_id:
                # Sans utilisateur connecté, on retourne un filtre impossible
                return FilterGroup[Rule](
                    filters=[
                        FilterBy[Rule](
                            field="status",
                            operator=Operator.EQ,
                            value="__NO_ACCESS__",
                        )
                    ],
                    use_or=False,
                )
            # DRAFT + créé par l'utilisateur
            return FilterGroup[Rule](
                filters=[
                    FilterBy[Rule](
                        field="status",
                        operator=Operator.EQ,
                        value=RuleStatus.DRAFT.value,
                    ),
                    FilterBy[Rule](
                        field="created_by_user_id",
                        operator=Operator.EQ,
                        value=current_user_id,
                    ),
                ],
                use_or=False,  # AND logic
            )

        # Pour les autres statuts (publics), pas de restriction
        return FilterGroup[Rule](
            filters=[
                FilterBy[Rule](
                    field="status",
                    operator=Operator.EQ,
                    value=status.value,
                )
            ],
            use_or=False,
        )

    def _build_default_status_filter(
        self,
        current_user_id: UUID | None,
    ) -> FilterGroup[Rule]:
        """
        Build default status filter.

        Logic:
        (status IN ['IN_PRODUCTION', 'TO_VALIDATE', 'ARCHIVED'])
        OR
        (status = 'DRAFT' AND created_by_user_id = current_user_id)
        """

        # Filtre pour les statuts publics
        public_status_filter = FilterBy[Rule](
            field="status",
            operator=Operator.IN,
            value=PUBLIC_STATUSES,
        )

        if not current_user_id:
            # Sans utilisateur, uniquement les statuts publics
            return FilterGroup[Rule](
                filters=[public_status_filter],
                use_or=False,
            )

        # Groupe pour DRAFT du créateur (AND entre status et created_by)
        draft_owner_filter = FilterGroup[Rule](
            filters=[
                FilterBy[Rule](
                    field="status",
                    operator=Operator.EQ,
                    value=RuleStatus.DRAFT.value,
                ),
                FilterBy[Rule](
                    field="created_by_user_id",
                    operator=Operator.EQ,
                    value=current_user_id,
                ),
            ],
            use_or=False,  # AND: status = DRAFT AND created_by = user
        )

        # Groupe final : publics OR (draft ET créateur)
        return FilterGroup[Rule](
            filters=[public_status_filter, draft_owner_filter],
            use_or=True,  # OR logic
        )
