"""Generic SQLAlchemy repository for aggregate roots."""

from collections.abc import Iterable, Mapping
from typing import Any, ClassVar

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.aggregate_root import AggregateRoot
from core.domain.identifier import EntityId
from core.domain.pagination import Page, PageParams, Sort, SortDirection
from core.infrastructure.db.base import Base
from core.infrastructure.db.mapper import EntityMapper
from core.infrastructure.db.query import build_filters, build_order_by, build_search
from core.infrastructure.db.tracker import AggregateTracker

DEFAULT_SORT = Sort("created_at", SortDirection.DESC)


class UntrackedAggregateError(RuntimeError):
    """`save` or `delete` received an aggregate not loaded or added in this request."""


class SqlaRepository[TEntity: AggregateRoot[Any, Any], TModel: Base]:
    """
    Persistence and paginated listing of one aggregate type.

    The repository keeps the ORM model behind every aggregate it adds or loads
    during the request. `save` writes the aggregate onto that same model, so only
    changed columns are updated and the version read by the request is checked
    (see `VersionMixin`); `delete` removes that model at flush time. Aggregates
    must therefore be loaded or added through the repository before being saved
    or deleted.

    Subclasses declare the columns clients may sort, filter and search on. Every
    aggregate returned by the repository is tracked so that the unit of work
    publishes its domain events.
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
        mapper_info = inspect(model)
        self._primary_key = mapper_info.primary_key[0]
        self._primary_key_attribute = mapper_info.get_property_by_column(
            self._primary_key
        ).key
        self._models: dict[object, TModel] = {}

    async def add(self, entity: TEntity) -> None:
        model = self._mapper.to_model(entity)
        self._session.add(model)
        self._models[entity.id_.value] = model
        self._tracker.track(entity)

    async def save(self, entity: TEntity) -> None:
        self._mapper.apply(entity, self._model_of(entity))
        self._tracker.track(entity)

    async def delete(self, entity: TEntity) -> None:
        model = self._models.pop(entity.id_.value, None)
        if model is None:
            raise self._untracked(entity)
        if inspect(model).pending:
            self._session.expunge(model)
        else:
            await self._session.delete(model)
        self._tracker.track(entity)

    async def get_by_id(
        self, entity_id: EntityId, *, lock: bool = False
    ) -> TEntity | None:
        """
        Load an aggregate.

        `lock=True` takes a shared row lock (`FOR SHARE`) held until the end of the
        transaction: concurrent updates and deletes of that row wait for it.
        """
        statement = select(self._model).where(self._primary_key == entity_id.value)
        if lock:
            statement = statement.with_for_update(read=True)
        model = await self._session.scalar(statement)
        return None if model is None else self._load(model)

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
            items=self._load_all(models),
            total=total,
            page=params.page,
            size=params.size,
        )

    def _load(self, model: TModel) -> TEntity:
        """Remember a loaded model and return its tracked aggregate."""
        self._models[getattr(model, self._primary_key_attribute)] = model
        entity = self._mapper.to_entity(model)
        self._tracker.track(entity)
        return entity

    def _load_all(self, models: Iterable[TModel]) -> list[TEntity]:
        return [self._load(model) for model in models]

    def _model_of(self, entity: TEntity) -> TModel:
        model = self._models.get(entity.id_.value)
        if model is None:
            raise self._untracked(entity)
        return model

    def _untracked(self, entity: TEntity) -> UntrackedAggregateError:
        return UntrackedAggregateError(
            f"{type(entity).__name__} '{entity.id_.value}' was not loaded or added "
            "by this repository in the current request."
        )
