"""Wiring of domain events to the handlers that react to them."""

from dishka import Provider, Scope, provide

from core.application.event_bus import EventHandlerRegistry
from modules.projects.public import ProjectArchived, ProjectDeleted
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)


class EventHandlersProvider(Provider):
    """Register here every handler that must run when a domain event is published."""

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={
                ProjectArchived: (CancelTasksOnProjectArchived,),
                ProjectDeleted: (DeleteTasksOnProjectDeleted,),
            }
        )
