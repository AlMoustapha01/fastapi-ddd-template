"""Delete a project."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.projects.domain.errors import ProjectNotFoundError
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteProjectRequest:
    project_id: UUID


class DeleteProjectCommand:
    """Delete a project and publish `ProjectDeleted`."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: DeleteProjectRequest) -> None:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        project.mark_deleted()
        await self._repository.delete(project)
        await self._uow.commit()
        log.info("Project deleted: %s", request.project_id)
