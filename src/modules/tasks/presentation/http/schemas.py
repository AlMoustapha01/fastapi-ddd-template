"""HTTP models of the tasks module."""

from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects.task_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.tasks.domain.value_objects.task_title import (
    MAX_LENGTH as TITLE_MAX_LENGTH,
)

SORT_DESCRIPTION: Final[str] = (
    "Field to sort by, prefixed with '-' for descending order. "
    "Allowed: title, status, created_at, updated_at."
)


class CreateTaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)


class UpdateTaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ChangeTaskStatusBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
