"""Rule audit event repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.db.repository.errors import EntityQueryError, EntitySaveError
from core.lib.db.repository.paginated import Paginated, PaginatedQueryParams
from modules.rules.domain.enums import RuleEventType
from modules.rules.domain.events import RuleEvent
from modules.rules.domain.ports import RuleAuditRepositoryPort
from modules.rules.infrastructure.mappers import RuleAuditEventMapper
from modules.rules.infrastructure.models import RuleAuditEventModel


class RuleAuditRepository(RuleAuditRepositoryPort):
    """Repository implementation for Rule audit events."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the repository.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.mapper = RuleAuditEventMapper()

    async def save(self, event: RuleEvent) -> None:
        """
        Save a single audit event.

        Args:
            event: The domain event to persist

        Raises:
            EntitySaveError: If the save operation fails
        """
        try:
            model = self.mapper.to_model(event)
            self.session.add(model)
            await self.session.flush()
        except SQLAlchemyError as e:
            raise EntitySaveError(
                entity_type="RuleAuditEvent",
                cause=e,
                details={
                    "event_id": str(event.event_id),
                    "rule_id": str(event.rule_id),
                },
            ) from e

    async def save_many(self, events: list[RuleEvent]) -> None:
        """
        Save multiple audit events in a batch.

        Args:
            events: List of domain events to persist

        Raises:
            EntitySaveError: If the save operation fails
        """
        if not events:
            return

        try:
            models = [self.mapper.to_model(event) for event in events]
            self.session.add_all(models)
            await self.session.flush()
        except SQLAlchemyError as e:
            raise EntitySaveError(
                entity_type="RuleAuditEvent",
                cause=e,
                details={"count": len(events)},
            ) from e

    async def find_by_rule_id(
        self,
        rule_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuleEvent]:
        """
        Get all audit events for a Rule, ordered by occurrence time desc.

        Args:
            rule_id: The rule ID to filter by
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of audit events for the rule
        """
        try:
            stmt = (
                select(RuleAuditEventModel)
                .where(RuleAuditEventModel.rule_id == rule_id)
                .order_by(RuleAuditEventModel.occurred_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.scalars(stmt)
            models = result.all()
            return [self.mapper.reconstruct_event(model) for model in models]
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="find by rule_id",
                cause=e,
                details={"rule_id": str(rule_id)},
            ) from e

    async def find_by_user(
        self,
        user_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuleEvent]:
        """
        Get all audit events performed by a user.

        Args:
            user_id: The user ID to filter by
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of audit events performed by the user
        """
        try:
            stmt = (
                select(RuleAuditEventModel)
                .where(RuleAuditEventModel.performed_by_user_id == user_id)
                .order_by(RuleAuditEventModel.occurred_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.scalars(stmt)
            models = result.all()
            return [self.mapper.reconstruct_event(model) for model in models]
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="find by user",
                cause=e,
                details={"user_id": str(user_id)},
            ) from e

    async def find_by_date_range(
        self,
        *,
        start_date: datetime,
        end_date: datetime,
        rule_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RuleEvent]:
        """
        Get audit events within a date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range
            rule_id: Optional rule ID to filter by
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of audit events within the date range
        """
        try:
            conditions = [
                RuleAuditEventModel.occurred_at >= start_date,
                RuleAuditEventModel.occurred_at <= end_date,
            ]

            if rule_id is not None:
                conditions.append(RuleAuditEventModel.rule_id == rule_id)

            stmt = (
                select(RuleAuditEventModel)
                .where(and_(*conditions))
                .order_by(RuleAuditEventModel.occurred_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.scalars(stmt)
            models = result.all()
            return [self.mapper.reconstruct_event(model) for model in models]
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="find by date range",
                cause=e,
                details={
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "rule_id": str(rule_id) if rule_id else None,
                },
            ) from e

    async def count_by_rule_id(self, rule_id: UUID) -> int:
        """
        Count total audit events for a Rule.

        Args:
            rule_id: The rule ID to count events for

        Returns:
            Total number of audit events for the rule
        """
        try:
            stmt = (
                select(func.count())
                .select_from(RuleAuditEventModel)
                .where(RuleAuditEventModel.rule_id == rule_id)
            )
            result = await self.session.scalar(stmt)
            return result or 0
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="count by rule_id",
                cause=e,
                details={"rule_id": str(rule_id)},
            ) from e

    async def find_all_paginated(
        self,
        params: PaginatedQueryParams[RuleEvent],
        rule_id: UUID,
    ) -> Paginated[RuleEvent]:
        """
        Get paginated audit events for a Rule.

        Args:
            params: Pagination and filter parameters
            rule_id: The rule ID to filter by

        Returns:
            Paginated audit events for the rule
        """
        try:
            # Get total count
            count = await self.count_by_rule_id(rule_id)

            # Calculate offset
            offset = (params.page - 1) * params.limit

            # Build query
            stmt = (
                select(RuleAuditEventModel)
                .where(RuleAuditEventModel.rule_id == rule_id)
                .order_by(RuleAuditEventModel.occurred_at.desc())
                .limit(params.limit)
                .offset(offset)
            )

            result = await self.session.scalars(stmt)
            models = result.all()
            events = tuple(self.mapper.reconstruct_event(model) for model in models)

            return Paginated[RuleEvent](
                count=count,
                limit=params.limit,
                page=params.page,
                data=events,
            )
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="find all paginated",
                cause=e,
                details={"rule_id": str(rule_id), "page": params.page},
            ) from e

    async def get_rule_creators(
        self,
        rule_ids: list[UUID],
    ) -> dict[UUID, UUID]:
        """
        Get the creator user ID for multiple rules.

        Args:
            rule_ids: List of rule IDs

        Returns:
            Dictionary mapping rule_id to creator user_id
        """
        if not rule_ids:
            return {}

        try:
            # Get the CREATED event for each rule
            stmt = select(
                RuleAuditEventModel.rule_id,
                RuleAuditEventModel.performed_by_user_id,
            ).where(
                and_(
                    RuleAuditEventModel.rule_id.in_(rule_ids),
                    RuleAuditEventModel.event_type == RuleEventType.CREATED,
                )
            )
            result = await self.session.execute(stmt)
            rows = result.all()
            return {row.rule_id: row.performed_by_user_id for row in rows}
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="get rule creators",
                cause=e,
                details={"rule_ids_count": len(rule_ids)},
            ) from e

    async def get_rule_approvers(
        self,
        rule_ids: list[UUID],
    ) -> dict[UUID, UUID | None]:
        """
        Get the approver user ID for multiple rules.

        Args:
            rule_ids: List of rule IDs

        Returns:
            Dictionary mapping rule_id to approver user_id (None if not approved)
        """
        if not rule_ids:
            return {}

        try:
            # Get the APPROVED event for each rule
            stmt = select(
                RuleAuditEventModel.rule_id,
                RuleAuditEventModel.performed_by_user_id,
            ).where(
                and_(
                    RuleAuditEventModel.rule_id.in_(rule_ids),
                    RuleAuditEventModel.event_type == RuleEventType.APPROVED,
                )
            )
            result = await self.session.execute(stmt)
            rows = result.all()

            # Initialize all rules with None
            approvers = dict.fromkeys(rule_ids)

            # Update with actual approvers
            for row in rows:
                approvers[row.rule_id] = row.performed_by_user_id

            return approvers
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type="RuleAuditEvent",
                operation="get rule approvers",
                cause=e,
                details={"rule_ids_count": len(rule_ids)},
            ) from e
