"""SqlaTaskRepository against PostgreSQL."""

from collections.abc import Sequence
from uuid import uuid4

from dishka import AsyncContainer

from core.application.unit_of_work import UnitOfWork
from core.domain.pagination import PageParams
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort


async def persist(container: AsyncContainer, tasks: Sequence[Task]) -> None:
    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        for task in tasks:
            await repository.add(task)
        await (await scope.get(UnitOfWork)).commit()


async def test_add_then_get_by_id_round_trips_every_field(
    container: AsyncContainer,
) -> None:
    task = Task.create(project_id=uuid4(), title="Draft", description="Text")
    task.start()
    await persist(container, [task])

    async with container() as scope:
        loaded = await (await scope.get(TaskRepositoryPort)).get_by_id(task.id_)

    assert loaded is not None
    assert loaded.props == task.props
    assert loaded.created_at_ == task.created_at_


async def test_list_open_by_project_returns_open_tasks_of_that_project(
    container: AsyncContainer,
) -> None:
    project_id = uuid4()
    todo = Task.create(project_id=project_id, title="Todo")
    started = Task.create(project_id=project_id, title="Started")
    started.start()
    done = Task.create(project_id=project_id, title="Done")
    done.complete()
    elsewhere = Task.create(project_id=uuid4(), title="Elsewhere")
    await persist(container, [todo, started, done, elsewhere])

    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        tasks = await repository.list_open_by_project(project_id)

    assert {task.id_ for task in tasks} == {todo.id_, started.id_}


async def test_delete_by_project_keeps_other_projects_tasks(
    container: AsyncContainer,
) -> None:
    project_id, other_project_id = uuid4(), uuid4()
    await persist(
        container,
        [
            Task.create(project_id=project_id, title="A"),
            Task.create(project_id=project_id, title="B"),
            Task.create(project_id=other_project_id, title="C"),
        ],
    )

    async with container() as scope:
        await (await scope.get(TaskRepositoryPort)).delete_by_project(project_id)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        removed = await repository.list_page(
            PageParams(), filters={"project_id": project_id}
        )
        kept = await repository.list_page(
            PageParams(), filters={"project_id": other_project_id}
        )
    assert (removed.total, kept.total) == (0, 1)


async def test_list_page_filters_by_project_and_status(
    container: AsyncContainer,
) -> None:
    project_id = uuid4()
    first = Task.create(project_id=project_id, title="First")
    first.complete()
    second = Task.create(project_id=project_id, title="Second")
    await persist(
        container, [first, second, Task.create(project_id=uuid4(), title="X")]
    )

    async with container() as scope:
        page = await (await scope.get(TaskRepositoryPort)).list_page(
            PageParams(),
            filters={"project_id": project_id, "status": TaskStatus.TODO.value},
        )

    assert [task.props.title.value for task in page.items] == ["Second"]
