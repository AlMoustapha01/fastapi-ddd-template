"""`ProjectLookupPort` backed by the public API of the projects module."""

from uuid import UUID

from modules.projects.public import ProjectsPublicApi
from modules.tasks.domain.ports import ProjectLookupPort, ProjectRef


class ProjectsModuleLookup(ProjectLookupPort):
    """Anti-corruption layer: translates `ProjectSummary` into `ProjectRef`."""

    def __init__(self, projects: ProjectsPublicApi) -> None:
        self._projects = projects

    async def get(self, project_id: UUID, *, lock: bool = False) -> ProjectRef | None:
        summary = await self._projects.get_summary(project_id, lock=lock)
        if summary is None:
            return None
        return ProjectRef(id=summary.id, is_active=summary.is_active)
