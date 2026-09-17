"""Cancel the open tasks of an archived project."""

import logging

from core.application.event_bus import EventHandler
from modules.projects.public import ProjectArchived
from modules.tasks.domain.ports import TaskRepositoryPort

log = logging.getLogger(__name__)


class CancelTasksOnProjectArchived(EventHandler[ProjectArchived]):
    """Runs in the transaction that archives the project; never commits."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, event: ProjectArchived) -> None:
        tasks = await self._repository.list_open_by_project(event.project_id)
        for task in tasks:
            task.cancel()
            await self._repository.save(task)
        log.info(
            "Cancelled %d task(s) of archived project %s", len(tasks), event.project_id
        )
