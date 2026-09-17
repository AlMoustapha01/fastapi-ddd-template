"""Value objects and aggregate of the projects module."""

from collections.abc import Callable

import pytest

from core.domain.errors import DomainValidationError
from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectAlreadyArchivedError,
    ProjectArchivedError,
)
from modules.projects.domain.events import (
    ProjectArchived,
    ProjectCreated,
    ProjectDeleted,
)
from modules.projects.domain.value_objects import ProjectDescription, ProjectName
from modules.projects.domain.value_objects.project_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.projects.domain.value_objects.project_name import (
    MAX_LENGTH as NAME_MAX_LENGTH,
)
from tests.unit.projects.factories import PAST, make_project


class TestProjectName:
    def test_strips_surrounding_whitespace(self) -> None:
        assert ProjectName("  Website  ").value == "Website"

    @pytest.mark.parametrize("raw", ["", "   ", "x" * (NAME_MAX_LENGTH + 1)])
    def test_rejects_invalid_length(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            ProjectName(raw)

        assert exc_info.value.code == "invalid_project_name"


class TestProjectDescription:
    def test_accepts_blank_text(self) -> None:
        assert not ProjectDescription("   ").value

    def test_rejects_too_long_text(self) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            ProjectDescription("x" * (DESCRIPTION_MAX_LENGTH + 1))

        assert exc_info.value.code == "invalid_project_description"


class TestProjectCreation:
    def test_create_builds_an_active_project_and_records_an_event(self) -> None:
        project = Project.create(name=" Website ", description="Marketing site")

        assert project.is_active
        assert project.props.name == ProjectName("Website")
        assert project.props.description == ProjectDescription("Marketing site")
        [event] = project.pull_events()
        assert isinstance(event, ProjectCreated)
        assert event.project_id == project.id_.value
        assert event.name == "Website"


class TestProjectChanges:
    def test_rename(self) -> None:
        project = make_project()

        project.rename("Intranet")

        assert project.props.name == ProjectName("Intranet")
        assert project.updated_at_ > PAST

    def test_change_description(self) -> None:
        project = make_project()

        project.change_description("New description")

        assert project.props.description == ProjectDescription("New description")
        assert project.updated_at_ > PAST

    def test_archive_changes_status_and_records_an_event(self) -> None:
        project = make_project()

        project.archive()

        assert project.props.status is ProjectStatus.ARCHIVED
        assert not project.is_active
        assert project.updated_at_ > PAST
        [event] = project.pull_events()
        assert isinstance(event, ProjectArchived)
        assert event.project_id == project.id_.value

    def test_archiving_twice_is_rejected(self) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectAlreadyArchivedError):
            project.archive()

    @pytest.mark.parametrize(
        "change",
        [
            lambda project: project.rename("Other"),
            lambda project: project.change_description("Other"),
        ],
    )
    def test_archived_project_is_read_only(
        self, change: Callable[[Project], None]
    ) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectArchivedError):
            change(project)

    def test_mark_deleted_records_an_event(self) -> None:
        project = make_project()

        project.mark_deleted()

        [event] = project.pull_events()
        assert isinstance(event, ProjectDeleted)
        assert event.project_id == project.id_.value
