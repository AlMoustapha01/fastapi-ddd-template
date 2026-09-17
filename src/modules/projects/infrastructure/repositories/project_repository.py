"""SQLAlchemy repository of projects."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.db.repository import SqlaRepository
from core.infrastructure.db.tracker import AggregateTracker
from modules.projects.domain.entities import Project
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId, ProjectName
from modules.projects.infrastructure.mappers import ProjectMapper
from modules.projects.infrastructure.models import ProjectModel


class SqlaProjectRepository(
    SqlaRepository[Project, ProjectModel], ProjectRepositoryPort
):
    sortable_fields = frozenset({"name", "created_at", "updated_at"})
    filterable_fields = frozenset({"status"})
    searchable_fields = ("name",)

    def __init__(self, session: AsyncSession, tracker: AggregateTracker) -> None:
        super().__init__(
            session=session, tracker=tracker, model=ProjectModel, mapper=ProjectMapper()
        )

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool:
        statement = select(ProjectModel.id).where(ProjectModel.name == name.value)
        if exclude_id is not None:
            statement = statement.where(ProjectModel.id != exclude_id.value)
        return await self._session.scalar(statement.limit(1)) is not None
