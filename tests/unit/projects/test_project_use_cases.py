"""Commands, queries and public API of the projects module."""

from uuid import uuid4

import pytest

from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
    CreateProjectCommand,
    CreateProjectRequest,
    DeleteProjectCommand,
    DeleteProjectRequest,
    UpdateProjectCommand,
    UpdateProjectRequest,
)
from modules.projects.application.dto import ProjectDTO
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
    ListProjectsQuery,
    ListProjectsRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectArchivedError,
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
)
from modules.projects.domain.events import ProjectArchived, ProjectDeleted
from modules.projects.public import ProjectsPublicApi, ProjectSummary
from tests.fakes.projects import InMemoryProjectRepository
from tests.fakes.unit_of_work import FakeUnitOfWork
from tests.unit.projects.factories import make_project


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


class TestCreateProject:
    async def test_creates_an_active_project(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryProjectRepository()

        result = await CreateProjectCommand(repository, uow).execute(
            CreateProjectRequest(name="Website", description="Marketing site")
        )

        assert (result.name, result.description) == ("Website", "Marketing site")
        assert result.status is ProjectStatus.ACTIVE
        assert result.id in repository.projects
        assert uow.commits == 1

    async def test_rejects_a_name_already_used(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryProjectRepository(make_project(name="Website"))

        with pytest.raises(ProjectNameAlreadyExistsError):
            await CreateProjectCommand(repository, uow).execute(
                CreateProjectRequest(name="  Website ")
            )

        assert uow.commits == 0


class TestUpdateProject:
    async def test_updates_name_and_description(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        result = await UpdateProjectCommand(repository, uow).execute(
            UpdateProjectRequest(
                project_id=project.id_.value, name="Intranet", description="Internal"
            )
        )

        assert (result.name, result.description) == ("Intranet", "Internal")
        assert uow.commits == 1

    async def test_keeping_the_same_name_is_allowed(self, uow: FakeUnitOfWork) -> None:
        project = make_project(name="Website")
        repository = InMemoryProjectRepository(project)

        result = await UpdateProjectCommand(repository, uow).execute(
            UpdateProjectRequest(project_id=project.id_.value, name="Website")
        )

        assert result.name == "Website"

    async def test_rejects_a_name_used_by_another_project(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = make_project(name="Website")
        repository = InMemoryProjectRepository(project, make_project(name="Intranet"))

        with pytest.raises(ProjectNameAlreadyExistsError):
            await UpdateProjectCommand(repository, uow).execute(
                UpdateProjectRequest(project_id=project.id_.value, name="Intranet")
            )

        assert uow.commits == 0

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await UpdateProjectCommand(InMemoryProjectRepository(), uow).execute(
                UpdateProjectRequest(project_id=uuid4(), name="Other")
            )

    async def test_archived_project_cannot_be_updated(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectArchivedError):
            await UpdateProjectCommand(InMemoryProjectRepository(project), uow).execute(
                UpdateProjectRequest(project_id=project.id_.value, description="x")
            )


class TestArchiveProject:
    async def test_archives_and_commits(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        result = await ArchiveProjectCommand(repository, uow).execute(
            ArchiveProjectRequest(project_id=project.id_.value)
        )

        assert result.status is ProjectStatus.ARCHIVED
        assert uow.commits == 1
        assert [type(event) for event in project.pull_events()] == [ProjectArchived]

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await ArchiveProjectCommand(InMemoryProjectRepository(), uow).execute(
                ArchiveProjectRequest(project_id=uuid4())
            )


class TestDeleteProject:
    async def test_deletes_and_records_an_event(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        await DeleteProjectCommand(repository, uow).execute(
            DeleteProjectRequest(project_id=project.id_.value)
        )

        assert repository.deleted == [project]
        assert repository.projects == {}
        assert uow.commits == 1
        assert [type(event) for event in project.pull_events()] == [ProjectDeleted]

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await DeleteProjectCommand(InMemoryProjectRepository(), uow).execute(
                DeleteProjectRequest(project_id=uuid4())
            )


class TestProjectQueries:
    async def test_get_by_id(self) -> None:
        project = make_project(name="Website")

        result = await GetProjectByIdQuery(InMemoryProjectRepository(project)).execute(
            GetProjectByIdRequest(project_id=project.id_.value)
        )

        assert result == ProjectDTO.from_entity(project)

    async def test_get_unknown_project(self) -> None:
        with pytest.raises(ProjectNotFoundError):
            await GetProjectByIdQuery(InMemoryProjectRepository()).execute(
                GetProjectByIdRequest(project_id=uuid4())
            )

    async def test_list_translates_the_request_for_the_repository(self) -> None:
        repository = InMemoryProjectRepository(
            make_project(name="Alpha"), make_project(name="Beta")
        )

        page = await ListProjectsQuery(repository).execute(
            ListProjectsRequest(
                page=1, size=1, status=ProjectStatus.ACTIVE, search="Al", sort="name"
            )
        )

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=1),
                "sort": Sort("name", SortDirection.ASC),
                "filters": {"status": "active"},
                "search": "Al",
            }
        ]
        assert (page.total, page.pages) == (2, 2)
        assert all(isinstance(item, ProjectDTO) for item in page.items)

    async def test_list_defaults(self) -> None:
        repository = InMemoryProjectRepository()

        await ListProjectsQuery(repository).execute(ListProjectsRequest())

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=20),
                "sort": Sort("created_at", SortDirection.DESC),
                "filters": {},
                "search": None,
            }
        ]


class TestProjectsPublicApi:
    async def test_returns_a_summary(self) -> None:
        project = make_project(name="Website", status=ProjectStatus.ARCHIVED)
        api = ProjectsPublicApi(InMemoryProjectRepository(project))

        summary = await api.get_summary(project.id_.value)

        assert summary == ProjectSummary(
            id=project.id_.value, name="Website", is_active=False
        )

    async def test_can_lock_the_project(self) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        await ProjectsPublicApi(repository).get_summary(project.id_.value, lock=True)

        assert repository.locked == [project.id_.value]

    async def test_returns_none_for_an_unknown_project(self) -> None:
        api = ProjectsPublicApi(InMemoryProjectRepository())

        assert await api.get_summary(uuid4()) is None
