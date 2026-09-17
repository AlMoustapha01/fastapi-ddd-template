"""Create a project."""

import logging
from dataclasses import dataclass

from core.application.unit_of_work import UnitOfWork
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.entities import Project
from modules.projects.domain.errors import ProjectNameAlreadyExistsError
from modules.projects.domain.ports import ProjectRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateProjectRequest:
    name: str
    description: str = ""


class CreateProjectCommand:
    """Create an active project. Project names are unique."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: CreateProjectRequest) -> ProjectDTO:
        project = Project.create(name=request.name, description=request.description)
        if await self._repository.exists_by_name(project.props.name):
            raise ProjectNameAlreadyExistsError(project.props.name.value)
        await self._repository.add(project)
        await self._uow.commit()
        log.info("Project created: %s", project.id_.value)
        return ProjectDTO.from_entity(project)
