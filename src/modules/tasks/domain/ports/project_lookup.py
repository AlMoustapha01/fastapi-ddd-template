"""What the tasks module needs to know about projects (owned by `tasks`)."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectRef:
    id: UUID
    is_active: bool


class ProjectLookupPort(Protocol):
    async def get(self, project_id: UUID) -> ProjectRef | None: ...
