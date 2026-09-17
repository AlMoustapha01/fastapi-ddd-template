"""SqlaProjectRepository and the unit of work against PostgreSQL."""

from collections.abc import Sequence

import pytest
from dishka import AsyncContainer

from core.application.unit_of_work import UnitOfWork
from core.domain.errors import ConflictError, DomainValidationError
from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectName


async def persist(container: AsyncContainer, projects: Sequence[Project]) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        for project in projects:
            await repository.add(project)
        await (await scope.get(UnitOfWork)).commit()


async def test_add_then_get_by_id_round_trips_every_field(
    container: AsyncContainer,
) -> None:
    project = Project.create(name="Website", description="Marketing site")
    await persist(container, [project])

    async with container() as scope:
        loaded = await (await scope.get(ProjectRepositoryPort)).get_by_id(project.id_)

    assert loaded is not None
    assert loaded.props == project.props
    assert loaded.created_at_ == project.created_at_
    assert loaded.updated_at_ == project.updated_at_


async def test_save_persists_changes(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        loaded = await repository.get_by_id(project.id_)
        assert loaded is not None
        loaded.rename("Intranet")
        loaded.archive()
        await repository.save(loaded)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        reloaded = await (await scope.get(ProjectRepositoryPort)).get_by_id(project.id_)
    assert reloaded is not None
    assert reloaded.props.name == ProjectName("Intranet")
    assert reloaded.props.status is ProjectStatus.ARCHIVED


async def test_delete_removes_the_row(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        loaded = await repository.get_by_id(project.id_)
        assert loaded is not None
        await repository.delete(loaded)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        assert await repository.get_by_id(project.id_) is None


async def test_exists_by_name_can_exclude_a_project(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        assert await repository.exists_by_name(ProjectName("Website"))
        assert not await repository.exists_by_name(
            ProjectName("Website"), exclude_id=project.id_
        )
        assert not await repository.exists_by_name(ProjectName("Intranet"))


async def test_unique_name_violation_is_reported_as_a_conflict(
    container: AsyncContainer,
) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        await repository.add(Project.create(name="Website"))
        await repository.add(Project.create(name="Website"))
        with pytest.raises(ConflictError) as exc_info:
            await (await scope.get(UnitOfWork)).commit()

    assert exc_info.value.code == "unique_violation"
    assert exc_info.value.details == {"constraint": "uq_projects_name"}


async def test_list_page_filters_sorts_and_paginates(container: AsyncContainer) -> None:
    alpha, beta, gamma = (
        Project.create(name=name) for name in ("Alpha", "Beta", "Gamma")
    )
    beta.archive()
    await persist(container, [gamma, alpha, beta])

    async with container() as scope:
        page = await (await scope.get(ProjectRepositoryPort)).list_page(
            PageParams(page=2, size=1),
            sort=Sort("name", SortDirection.ASC),
            filters={"status": ProjectStatus.ACTIVE.value},
        )

    assert [project.props.name.value for project in page.items] == ["Gamma"]
    assert (page.total, page.pages) == (2, 2)


async def test_list_page_search_matches_wildcards_literally(
    container: AsyncContainer,
) -> None:
    await persist(
        container, [Project.create(name="50% off"), Project.create(name="500 offers")]
    )

    async with container() as scope:
        page = await (await scope.get(ProjectRepositoryPort)).list_page(
            PageParams(), search="50%"
        )

    assert [project.props.name.value for project in page.items] == ["50% off"]


async def test_list_page_rejects_a_field_outside_the_whitelist(
    container: AsyncContainer,
) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        with pytest.raises(DomainValidationError):
            await repository.list_page(PageParams(), sort=Sort("description"))
