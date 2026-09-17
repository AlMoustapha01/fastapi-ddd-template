"""Mapping between `Task` and `TaskModel`."""

from core.infrastructure.db.mapper import EntityMapper
from modules.tasks.domain.entities import Task, TaskProps
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle
from modules.tasks.infrastructure.models import TaskModel


class TaskMapper(EntityMapper[Task, TaskModel]):
    def to_model(self, entity: Task) -> TaskModel:
        model = TaskModel(id=entity.id_.value)
        self.apply(entity, model)
        return model

    def apply(self, entity: Task, model: TaskModel) -> None:
        model.project_id = entity.props.project_id
        model.title = entity.props.title.value
        model.description = entity.props.description.value
        model.status = entity.props.status.value
        model.created_at = entity.created_at_
        model.updated_at = entity.updated_at_

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
