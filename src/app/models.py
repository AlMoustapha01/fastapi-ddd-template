"""Import every ORM model so that `Base.metadata` describes the whole schema."""

from core.infrastructure.db.base import Base
from modules.projects.infrastructure.models import ProjectModel
from modules.tasks.infrastructure.models import TaskModel

__all__ = ["Base", "ProjectModel", "TaskModel"]
