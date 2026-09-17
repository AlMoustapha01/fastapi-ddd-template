"""Dishka provider of the projects module."""

from dishka import Provider, Scope, provide, provide_all

from modules.projects.application.commands import (
    ArchiveProjectCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    UpdateProjectCommand,
)
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    ListProjectsQuery,
)
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.infrastructure.repositories import SqlaProjectRepository
from modules.projects.public import ProjectsPublicApi


class ProjectsProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(SqlaProjectRepository, provides=ProjectRepositoryPort)
    use_cases = provide_all(
        CreateProjectCommand,
        UpdateProjectCommand,
        ArchiveProjectCommand,
        DeleteProjectCommand,
        GetProjectByIdQuery,
        ListProjectsQuery,
    )
    public_api = provide(ProjectsPublicApi)
