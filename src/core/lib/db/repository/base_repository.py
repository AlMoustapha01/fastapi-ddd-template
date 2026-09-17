"""Base repository implementation for domain entities."""

from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import Select, and_, delete, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.lib.base.entity import Entity
from core.lib.db.model_base import Base

from .base_repository_port import BaseRepositoryPort
from .entity_mapper_port import EntityMapperPort
from .errors import (
    EntityAddError,
    EntityDeleteError,
    EntityQueryError,
    EntitySaveError,
)
from .paginated import (
    FilterBy,
    FilterGroup,
    Operator,
    Paginated,
    PaginatedQueryParams,
    SortOrder,
)

T = TypeVar("T", bound=Entity[Any, Any])
M = TypeVar("M", bound=Base)

BTW_LEN = 2


class BaseRepository[T, M](BaseRepositoryPort[T]):
    """Base repository implementation with SQLAlchemy."""

    def __init__(
        self,
        session: AsyncSession,
        model: type[M],
        mapper: EntityMapperPort[T, M],
    ) -> None:
        self.session = session
        self.model = model
        self.mapper = mapper
        self._entity_name = model.__name__.replace("Model", "")

    async def add(self, entity: T | list[T]) -> None:
        """Add one or multiple domain entities to the session (no commit)."""
        try:
            entities = entity if isinstance(entity, list) else [entity]
            models = [self.mapper.to_model(e) for e in entities]
            self.session.add_all(models)
        except SQLAlchemyError as e:
            raise EntityAddError(
                entity_type=self._entity_name,
                cause=e,
                details={"count": len(entities)},
            ) from e

    async def save(self, entity: T | list[T]) -> None:
        """Update one or multiple existing entities (uses merge for upsert behavior).

        This method converts entities to models and merges them into the session.
        SQLAlchemy's merge will:
        - Update the entity if it exists in the database (based on primary key)
        - Insert it if it doesn't exist

        Note: This does not commit the transaction.
        """
        try:
            entities = entity if isinstance(entity, list) else [entity]
            models = [self.mapper.to_model(e) for e in entities]

            for model in models:
                await self.session.merge(model)

        except SQLAlchemyError as e:
            ids = []
            for e_item in entities:
                if hasattr(e_item, "id_"):
                    id_value = (
                        e_item.id_.value if hasattr(e_item.id_, "value") else e_item.id_
                    )
                    ids.append(str(id_value))

            raise EntitySaveError(
                entity_type=self._entity_name,
                cause=e,
                details={"ids": ids, "count": len(entities)},
            ) from e

    async def delete(self, entity: T | list[T]) -> None:
        """Delete one or multiple entities by their IDs."""
        try:
            entities = entity if isinstance(entity, list) else [entity]
            ids = [e.id_.value for e in entities]  # type: ignore[union-attr]
            stmt = delete(self.model).where(self.model.id.in_(ids))  # type: ignore[attr-defined]
            await self.session.execute(stmt)
        except SQLAlchemyError as e:
            raise EntityDeleteError(
                entity_type=self._entity_name,
                cause=e,
                details={"ids": [str(id_) for id_ in ids], "count": len(ids)},
            ) from e

    async def find_one_by_id(self, id_: Any) -> T | None:
        """Find a single entity by its ID."""
        try:
            id_value = id_.value if hasattr(id_, "value") else id_
            stmt = select(self.model).where(self.model.id == id_value)  # type: ignore[attr-defined]
            result = await self.session.scalar(stmt)
            return self.mapper.to_entity(result) if result else None
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find by id",
                cause=e,
                details={"id": str(id_value)},
            ) from e

    async def find_all_paginated(self, params: PaginatedQueryParams[T]) -> Paginated[T]:
        """Fetch entities with pagination, filtering and ordering."""
        try:
            stmt = select(self.model)
            filters = self._build_filters(params)
            stmt = self._apply_filters(stmt, filters)
            stmt = self._apply_order(stmt, params)

            total_count = await self._count_total(filters)
            stmt = self._apply_pagination(stmt, params)

            result: Sequence[M] = (await self.session.scalars(stmt)).all()
            entities = tuple(self.mapper.to_entity(m) for m in result)

            return Paginated(
                count=total_count,
                limit=params.limit,
                page=params.page,
                data=entities,
            )
        except SQLAlchemyError as e:
            raise EntityQueryError(
                entity_type=self._entity_name,
                operation="find paginated",
                cause=e,
                details={
                    "page": params.page,
                    "limit": params.limit,
                    "has_filters": bool(params.filter_by),
                    "has_ordering": bool(params.order_by),
                },
            ) from e

    def _build_filters(self, params: PaginatedQueryParams[T]) -> list[Any]:
        """Build SQLAlchemy filter conditions from params."""
        filters: list[Any] = []

        # Process regular filters (combined with AND)
        if params.filter_by:
            for f in params.filter_by:
                condition = self._build_filter_condition(f)
                if condition is not None:
                    filters.append(condition)

        # Process filter groups (combined with OR within group, AND between groups)
        if params.filter_groups:
            for group in params.filter_groups:
                group_condition = self._build_group_condition(group)
                if group_condition is not None:
                    filters.append(group_condition)

        return filters

    def _build_filter_condition(  # noqa: PLR0911
        self, f: FilterBy[T] | FilterGroup[T]
    ) -> Any | None:
        """Build a single filter condition, handling nested FilterGroups."""
        if isinstance(f, FilterGroup):
            return self._build_group_condition(f)

        # It's a FilterBy
        field = getattr(self.model, f.field, None)
        if field is None:
            return None

        match f.operator:
            case Operator.EQ:
                return field == f.value
            case Operator.IN:
                return field.in_(f.value)
            case Operator.BTW:
                if isinstance(f.value, (list, tuple)) and len(f.value) == BTW_LEN:
                    return field.between(f.value[0], f.value[1])
            case Operator.ILIKE:
                return field.ilike(f.value)
        return None

    def _build_group_condition(self, group: FilterGroup[T]) -> Any | None:
        """Build a group condition, recursively handling nested FilterGroups."""
        group_conditions: list[Any] = []

        for f in group.filters:
            condition = self._build_filter_condition(f)
            if condition is not None:
                group_conditions.append(condition)

        if not group_conditions:
            return None

        if group.use_or:
            return or_(*group_conditions)
        return and_(*group_conditions)

    def _apply_filters(
        self, stmt: Select[tuple[M]], filters: list[Any]
    ) -> Select[tuple[M]]:
        """Attach filters to a statement if any."""
        return stmt.where(and_(*filters)) if filters else stmt

    def _apply_order(
        self, stmt: Select[tuple[M]], params: PaginatedQueryParams[T]
    ) -> Select[tuple[M]]:
        """Attach ORDER BY clause."""
        if not params.order_by or not params.order_by.field:
            return stmt

        field = getattr(self.model, params.order_by.field, None)
        if field is None:
            return stmt

        return stmt.order_by(
            field.desc() if params.order_by.param == SortOrder.DESC else field.asc()
        )

    def _apply_pagination(
        self, stmt: Select[tuple[M]], params: PaginatedQueryParams[T]
    ) -> Select[tuple[M]]:
        """Apply OFFSET/LIMIT for pagination."""
        offset = (params.page - 1) * params.limit
        return stmt.offset(offset).limit(params.limit)

    async def _count_total(self, filters: list[Any]) -> int:
        """Count total results matching filters."""
        count_stmt = select(func.count()).select_from(self.model)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        return await self.session.scalar(count_stmt) or 0
