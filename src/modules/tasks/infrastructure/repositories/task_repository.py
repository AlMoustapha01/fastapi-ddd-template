"""SQLAlchemy repository of tasks."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.db.repository import SqlaRepository
from core.infrastructure.db.tracker import AggregateTracker
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.infrastructure.mappers import TaskMapper
from modules.tasks.infrastructure.models import TaskModel

OPEN_STATUSES = [status.value for status in TaskStatus if not status.is_terminal]


class SqlaTaskRepository(SqlaRepository[Task, TaskModel], TaskRepositoryPort):
    sortable_fields = frozenset({"title", "status", "created_at", "updated_at"})
    filterable_fields = frozenset({"project_id", "status"})

    def __init__(self, session: AsyncSession, tracker: AggregateTracker) -> None:
        super().__init__(
            session=session, tracker=tracker, model=TaskModel, mapper=TaskMapper()
        )

    async def list_open_by_project(self, project_id: UUID) -> list[Task]:
        statement = (
            select(TaskModel)
            .where(
                TaskModel.project_id == project_id,
                TaskModel.status.in_(OPEN_STATUSES),
            )
            .order_by(TaskModel.created_at, TaskModel.id)
        )
        models = (await self._session.scalars(statement)).all()
        tasks = [self._mapper.to_entity(model) for model in models]
        for task in tasks:
            self._tracker.track(task)
        return tasks

    async def delete_by_project(self, project_id: UUID) -> None:
        statement = delete(TaskModel).where(TaskModel.project_id == project_id)
        await self._session.execute(statement)
