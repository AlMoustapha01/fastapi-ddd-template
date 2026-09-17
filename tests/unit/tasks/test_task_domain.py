"""Value objects and lifecycle of the task aggregate."""

from collections.abc import Callable
from uuid import uuid4

import pytest

from core.domain.errors import DomainValidationError
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import InvalidTaskTransitionError, TaskClosedError
from modules.tasks.domain.value_objects import TaskDescription, TaskTitle
from modules.tasks.domain.value_objects.task_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.tasks.domain.value_objects.task_title import (
    MAX_LENGTH as TITLE_MAX_LENGTH,
)
from tests.unit.tasks.factories import PAST, make_task

TODO, IN_PROGRESS = TaskStatus.TODO, TaskStatus.IN_PROGRESS
DONE, CANCELLED = TaskStatus.DONE, TaskStatus.CANCELLED


class TestValueObjects:
    def test_title_is_stripped(self) -> None:
        assert TaskTitle("  Write copy ").value == "Write copy"

    @pytest.mark.parametrize("raw", ["", "  ", "x" * (TITLE_MAX_LENGTH + 1)])
    def test_title_length_is_validated(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            TaskTitle(raw)

        assert exc_info.value.code == "invalid_task_title"

    def test_description_length_is_validated(self) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            TaskDescription("x" * (DESCRIPTION_MAX_LENGTH + 1))

        assert exc_info.value.code == "invalid_task_description"


class TestTaskStatus:
    @pytest.mark.parametrize(
        ("status", "terminal"),
        [(TODO, False), (IN_PROGRESS, False), (DONE, True), (CANCELLED, True)],
    )
    def test_is_terminal(self, status: TaskStatus, terminal: bool) -> None:
        assert status.is_terminal is terminal


class TestTaskCreation:
    def test_create_builds_a_todo_task(self) -> None:
        project_id = uuid4()

        task = Task.create(project_id=project_id, title=" Draft ", description="Text")

        assert task.props.project_id == project_id
        assert task.props.title == TaskTitle("Draft")
        assert task.props.description == TaskDescription("Text")
        assert task.props.status is TODO


class TestTaskLifecycle:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (TODO, IN_PROGRESS),
            (TODO, DONE),
            (TODO, CANCELLED),
            (IN_PROGRESS, DONE),
            (IN_PROGRESS, CANCELLED),
        ],
    )
    def test_allowed_transitions(self, current: TaskStatus, target: TaskStatus) -> None:
        task = make_task(status=current)

        task.change_status(target)

        assert task.props.status is target
        assert task.updated_at_ > PAST

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (TODO, TODO),
            (IN_PROGRESS, TODO),
            (IN_PROGRESS, IN_PROGRESS),
            (DONE, TODO),
            (DONE, CANCELLED),
            (CANCELLED, DONE),
            (CANCELLED, IN_PROGRESS),
        ],
    )
    def test_forbidden_transitions(
        self, current: TaskStatus, target: TaskStatus
    ) -> None:
        task = make_task(status=current)

        with pytest.raises(InvalidTaskTransitionError) as exc_info:
            task.change_status(target)

        assert exc_info.value.details == {
            "task_id": str(task.id_.value),
            "current": current.value,
            "target": target.value,
        }
        assert task.props.status is current

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (Task.start, IN_PROGRESS),
            (Task.complete, DONE),
            (Task.cancel, CANCELLED),
        ],
    )
    def test_shortcuts(
        self, action: Callable[[Task], None], expected: TaskStatus
    ) -> None:
        task = make_task()

        action(task)

        assert task.props.status is expected


class TestTaskChanges:
    def test_rename_and_change_description(self) -> None:
        task = make_task()

        task.rename("New title")
        task.change_description("New description")

        assert task.props.title == TaskTitle("New title")
        assert task.props.description == TaskDescription("New description")
        assert task.updated_at_ > PAST

    @pytest.mark.parametrize("status", [DONE, CANCELLED])
    @pytest.mark.parametrize(
        "change",
        [
            lambda task: task.rename("Other"),
            lambda task: task.change_description("Other"),
        ],
    )
    def test_closed_task_cannot_be_modified(
        self, status: TaskStatus, change: Callable[[Task], None]
    ) -> None:
        task = make_task(status=status)

        with pytest.raises(TaskClosedError):
            change(task)
