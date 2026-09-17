"""HTTP models of the projects module."""

from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects.project_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.projects.domain.value_objects.project_name import (
    MAX_LENGTH as NAME_MAX_LENGTH,
)

SORT_DESCRIPTION: Final[str] = (
    "Field to sort by, prefixed with '-' for descending order. "
    "Allowed: name, created_at, updated_at."
)


class CreateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)


class UpdateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
