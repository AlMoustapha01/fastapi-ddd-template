"""Generic SQLAlchemy repository for aggregate roots."""

from collections.abc import Mapping
from typing import Any, ClassVar

from sqlalchemy import delete, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.aggregate_root import AggregateRoot
from core.domain.identifier import EntityId
from core.domain.pagination import Page, PageParams, Sort, SortDirection
from core.infrastructure.db.base import Base
from core.infrastructure.db.mapper import EntityMapper
from core.infrastructure.db.query import build_filters, build_order_by, build_search
from core.infrastructure.db.tracker import AggregateTracker

DEFAULT_SORT = Sort("created_at", SortDirection.DESC)


class SqlaRepository[TEntity: AggregateRoot[Any, Any], TModel: Base]:
    """
    Persistence and paginated listing of one aggregate type.

    Subclasses declare the columns clients may sort, filter and search on. Every
    aggregate added, saved, deleted or loaded by id is tracked so that the unit of
    work publishes its domain events.
    """

    sortable_fields: ClassVar[frozenset[str]] = frozenset({"created_at", "updated_at"})
    filterable_fields: ClassVar[frozenset[str]] = frozenset()
    searchable_fields: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        *,
        session: AsyncSession,
        tracker: AggregateTracker,
        model: type[TModel],
        mapper: EntityMapper[TEntity, TModel],
    ) -> None:
        self._session = session
        self._tracker = tracker
        self._model = model
        self._mapper = mapper

    async def add(self, entity: TEntity) -> None:
        self._session.add(self._mapper.to_model(entity))
        self._tracker.track(entity)

    async def save(self, entity: TEntity) -> None:
        await self._session.merge(self._mapper.to_model(entity))
        self._tracker.track(entity)

    async def delete(self, entity: TEntity) -> None:
        primary_key = inspect(self._model).primary_key[0]
        statement = delete(self._model).where(primary_key == entity.id_.value)
        await self._session.execute(statement)
        self._tracker.track(entity)

    async def get_by_id(self, entity_id: EntityId) -> TEntity | None:
        model = await self._session.get(self._model, entity_id.value)
        if model is None:
            return None
        entity = self._mapper.to_entity(model)
        self._tracker.track(entity)
        return entity

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[TEntity]:
        conditions = [
            *build_filters(self._model, filters or {}, allowed=self.filterable_fields),
            *build_search(self._model, search, fields=self.searchable_fields),
        ]
        order_by = build_order_by(
            self._model, sort or DEFAULT_SORT, allowed=self.sortable_fields
        )
        count = select(func.count()).select_from(self._model).where(*conditions)
        total = await self._session.scalar(count) or 0
        statement = (
            select(self._model)
            .where(*conditions)
            .order_by(*order_by)
            .offset(params.offset)
            .limit(params.size)
        )
        models = (await self._session.scalars(statement)).all()
        return Page(
            items=[self._mapper.to_entity(model) for model in models],
            total=total,
            page=params.page,
            size=params.size,
        )
