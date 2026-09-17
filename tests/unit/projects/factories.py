"""Builders of project aggregates for tests."""

from datetime import UTC, datetime

from modules.projects.domain.entities import Project, ProjectProps
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)

PAST = datetime(2000, 1, 1, tzinfo=UTC)


def make_project(
    *,
    name: str = "Website",
    description: str = "",
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> Project:
    """A project as loaded from storage: no pending event, timestamps in the past."""
    return Project(
        id_=ProjectId.generate(),
        props=ProjectProps(
            name=ProjectName(name),
            description=ProjectDescription(description),
            status=status,
        ),
        created_at_=PAST,
        updated_at_=PAST,
    )
