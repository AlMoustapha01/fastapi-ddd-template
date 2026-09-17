"""Update the name and/or description of a project."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.errors import (
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
)
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateProjectRequest:
    project_id: UUID
    name: str | None = None
    description: str | None = None


class UpdateProjectCommand:
    """Rename a project and/or change its description (active projects only)."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: UpdateProjectRequest) -> ProjectDTO:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        if request.name is not None:
            project.rename(request.name)
            if await self._repository.exists_by_name(
                project.props.name, exclude_id=project.id_
            ):
                raise ProjectNameAlreadyExistsError(project.props.name.value)
        if request.description is not None:
            project.change_description(request.description)
        await self._repository.save(project)
        await self._uow.commit()
        log.info("Project updated: %s", request.project_id)
        return ProjectDTO.from_entity(project)
