"""Delete the tasks of a deleted project."""

import logging

from core.application.event_bus import EventHandler
from modules.projects.public import ProjectDeleted
from modules.tasks.domain.ports import TaskRepositoryPort

log = logging.getLogger(__name__)


class DeleteTasksOnProjectDeleted(EventHandler[ProjectDeleted]):
    """Runs in the transaction that deletes the project; never commits."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, event: ProjectDeleted) -> None:
        await self._repository.delete_by_project(event.project_id)
        log.info("Deleted the tasks of project %s", event.project_id)
