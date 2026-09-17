"""Port interface for Rule audit event persistence."""

from abc import abstractmethod
from datetime import datetime
from typing import Protocol
from uuid import UUID

from core.lib.db.repository.paginated import Paginated, PaginatedQueryParams
from modules.rules.domain.events import RuleEvent


class RuleAuditRepositoryPort(Protocol):
    """Port interface for Rule audit event persistence."""

    @abstractmethod
    async def save(self, event: RuleEvent) -> None:
        """
        Save a single audit event.

        Args:
            event: The domain event to persist
        """
        ...

    @abstractmethod
    async def save_many(self, events: list[RuleEvent]) -> None:
        """
        Save multiple audit events in a batch.

        Args:
            events: List of domain events to persist
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def count_by_rule_id(self, rule_id: UUID) -> int:
        """
        Count total audit events for a Rule.

        Args:
            rule_id: The rule ID to count events for

        Returns:
            Total number of audit events for the rule
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...
