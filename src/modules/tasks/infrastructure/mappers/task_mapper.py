"""Mapping between `Task` and `TaskModel`."""

from core.infrastructure.db.mapper import EntityMapper
from modules.tasks.domain.entities import Task, TaskProps
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle
from modules.tasks.infrastructure.models import TaskModel


class TaskMapper(EntityMapper[Task, TaskModel]):
    def to_model(self, entity: Task) -> TaskModel:
        return TaskModel(
            id=entity.id_.value,
            project_id=entity.props.project_id,
            title=entity.props.title.value,
            description=entity.props.description.value,
            status=entity.props.status.value,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: TaskModel) -> Task:
        return Task(
            id_=TaskId(model.id),
            props=TaskProps(
                project_id=model.project_id,
                title=TaskTitle(model.title),
                description=TaskDescription(model.description),
                status=TaskStatus(model.status),
            ),
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
