"""Mapping between `Project` and `ProjectModel`."""

from core.infrastructure.db.mapper import EntityMapper
from modules.projects.domain.entities import Project, ProjectProps
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)
from modules.projects.infrastructure.models import ProjectModel


class ProjectMapper(EntityMapper[Project, ProjectModel]):
    def to_model(self, entity: Project) -> ProjectModel:
        return ProjectModel(
            id=entity.id_.value,
            name=entity.props.name.value,
            description=entity.props.description.value,
            status=entity.props.status.value,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: ProjectModel) -> Project:
        return Project(
            id_=ProjectId(model.id),
            props=ProjectProps(
                name=ProjectName(model.name),
                description=ProjectDescription(model.description),
                status=ProjectStatus(model.status),
            ),
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
