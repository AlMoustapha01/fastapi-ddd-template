"""Get one project."""

from dataclasses import dataclass
from uuid import UUID

from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.errors import ProjectNotFoundError
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId


@dataclass(frozen=True, slots=True, kw_only=True)
class GetProjectByIdRequest:
    project_id: UUID


class GetProjectByIdQuery:
    """Return one project."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: GetProjectByIdRequest) -> ProjectDTO:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        return ProjectDTO.from_entity(project)
