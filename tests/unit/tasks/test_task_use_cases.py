"""Commands, queries and event handlers of the tasks module."""

from uuid import uuid4

import pytest

from core.domain.errors import DomainValidationError
from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.public import ProjectArchived, ProjectDeleted
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
    CreateTaskCommand,
    CreateTaskRequest,
    DeleteTaskCommand,
    DeleteTaskRequest,
    UpdateTaskCommand,
    UpdateTaskRequest,
)
from modules.tasks.application.dto import TaskDTO
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)
from modules.tasks.application.queries import (
    GetTaskByIdQuery,
    GetTaskByIdRequest,
    ListTasksQuery,
    ListTasksRequest,
)
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import (
    InvalidTaskTransitionError,
    TaskClosedError,
    TaskNotFoundError,
    TaskProjectArchivedError,
    TaskProjectNotFoundError,
)
from modules.tasks.domain.ports import ProjectRef
from tests.fakes.tasks import FakeProjectLookup, InMemoryTaskRepository
from tests.fakes.unit_of_work import FakeUnitOfWork
from tests.unit.tasks.factories import make_task


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


class TestCreateTask:
    async def test_creates_a_task_in_an_active_project(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = ProjectRef(id=uuid4(), is_active=True)
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(project), uow)

        task = await command.execute(
            CreateTaskRequest(project_id=project.id, title=" Draft ")
        )

        assert (task.project_id, task.title, task.status) == (
            project.id,
            "Draft",
            TaskStatus.TODO,
        )
        assert task.id in repository.tasks
        assert uow.commits == 1

    async def test_locks_the_project_until_the_task_is_committed(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = ProjectRef(id=uuid4(), is_active=True)
        lookup = FakeProjectLookup(project)

        await CreateTaskCommand(InMemoryTaskRepository(), lookup, uow).execute(
            CreateTaskRequest(project_id=project.id, title="Draft")
        )

        assert lookup.locked == [project.id]

    async def test_unknown_project_is_rejected(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(), uow)

        with pytest.raises(TaskProjectNotFoundError):
            await command.execute(CreateTaskRequest(project_id=uuid4(), title="Draft"))

        assert repository.tasks == {}
        assert uow.commits == 0

    async def test_archived_project_is_rejected(self, uow: FakeUnitOfWork) -> None:
        project = ProjectRef(id=uuid4(), is_active=False)
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(project), uow)

        with pytest.raises(TaskProjectArchivedError):
            await command.execute(CreateTaskRequest(project_id=project.id, title="x"))

        assert repository.tasks == {}

    async def test_invalid_title_is_rejected(self, uow: FakeUnitOfWork) -> None:
        project = ProjectRef(id=uuid4(), is_active=True)
        command = CreateTaskCommand(
            InMemoryTaskRepository(), FakeProjectLookup(project), uow
        )

        with pytest.raises(DomainValidationError):
            await command.execute(CreateTaskRequest(project_id=project.id, title=" "))


class TestUpdateTask:
    async def test_updates_title_and_description(self, uow: FakeUnitOfWork) -> None:
        task = make_task()

        result = await UpdateTaskCommand(InMemoryTaskRepository(task), uow).execute(
            UpdateTaskRequest(
                task_id=task.id_.value, title="New title", description="Details"
            )
        )

        assert (result.title, result.description) == ("New title", "Details")
        assert uow.commits == 1

    async def test_closed_task_cannot_be_updated(self, uow: FakeUnitOfWork) -> None:
        task = make_task(status=TaskStatus.DONE)

        with pytest.raises(TaskClosedError):
            await UpdateTaskCommand(InMemoryTaskRepository(task), uow).execute(
                UpdateTaskRequest(task_id=task.id_.value, title="Other")
            )

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await UpdateTaskCommand(InMemoryTaskRepository(), uow).execute(
                UpdateTaskRequest(task_id=uuid4(), title="Other")
            )


class TestChangeTaskStatus:
    async def test_moves_the_task(self, uow: FakeUnitOfWork) -> None:
        task = make_task()

        result = await ChangeTaskStatusCommand(
            InMemoryTaskRepository(task), uow
        ).execute(
            ChangeTaskStatusRequest(task_id=task.id_.value, status=TaskStatus.DONE)
        )

        assert result.status is TaskStatus.DONE
        assert uow.commits == 1

    async def test_invalid_transition(self, uow: FakeUnitOfWork) -> None:
        task = make_task(status=TaskStatus.DONE)

        with pytest.raises(InvalidTaskTransitionError):
            await ChangeTaskStatusCommand(InMemoryTaskRepository(task), uow).execute(
                ChangeTaskStatusRequest(task_id=task.id_.value, status=TaskStatus.TODO)
            )

        assert uow.commits == 0

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await ChangeTaskStatusCommand(InMemoryTaskRepository(), uow).execute(
                ChangeTaskStatusRequest(task_id=uuid4(), status=TaskStatus.DONE)
            )


class TestDeleteTask:
    async def test_deletes_the_task(self, uow: FakeUnitOfWork) -> None:
        task = make_task()
        repository = InMemoryTaskRepository(task)

        await DeleteTaskCommand(repository, uow).execute(
            DeleteTaskRequest(task_id=task.id_.value)
        )

        assert repository.tasks == {}
        assert uow.commits == 1

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await DeleteTaskCommand(InMemoryTaskRepository(), uow).execute(
                DeleteTaskRequest(task_id=uuid4())
            )


class TestTaskQueries:
    async def test_get_by_id(self) -> None:
        task = make_task()

        result = await GetTaskByIdQuery(InMemoryTaskRepository(task)).execute(
            GetTaskByIdRequest(task_id=task.id_.value)
        )

        assert result == TaskDTO.from_entity(task)

    async def test_get_unknown_task(self) -> None:
        with pytest.raises(TaskNotFoundError):
            await GetTaskByIdQuery(InMemoryTaskRepository()).execute(
                GetTaskByIdRequest(task_id=uuid4())
            )

    async def test_list_translates_the_request_for_the_repository(self) -> None:
        project_id = uuid4()
        repository = InMemoryTaskRepository(make_task(), make_task())

        page = await ListTasksQuery(repository).execute(
            ListTasksRequest(
                page=1,
                size=10,
                project_id=project_id,
                status=TaskStatus.TODO,
                sort="title",
            )
        )

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=10),
                "sort": Sort("title", SortDirection.ASC),
                "filters": {"project_id": project_id, "status": "todo"},
                "search": None,
            }
        ]
        assert page.total == 2
        assert all(isinstance(item, TaskDTO) for item in page.items)


class TestEventHandlers:
    async def test_archived_project_cancels_only_its_open_tasks(self) -> None:
        project_id = uuid4()
        todo = make_task(project_id=project_id)
        started = make_task(project_id=project_id, status=TaskStatus.IN_PROGRESS)
        done = make_task(project_id=project_id, status=TaskStatus.DONE)
        other_project_task = make_task()
        repository = InMemoryTaskRepository(todo, started, done, other_project_task)

        await CancelTasksOnProjectArchived(repository).handle(
            ProjectArchived(project_id=project_id)
        )

        assert todo.props.status is TaskStatus.CANCELLED
        assert started.props.status is TaskStatus.CANCELLED
        assert done.props.status is TaskStatus.DONE
        assert other_project_task.props.status is TaskStatus.TODO

    async def test_deleted_project_removes_only_its_tasks(self) -> None:
        project_id = uuid4()
        other_project_task = make_task()
        repository = InMemoryTaskRepository(
            make_task(project_id=project_id),
            make_task(project_id=project_id, status=TaskStatus.DONE),
            other_project_task,
        )

        await DeleteTasksOnProjectDeleted(repository).handle(
            ProjectDeleted(project_id=project_id)
        )

        assert list(repository.tasks) == [other_project_task.id_.value]
