"""Every Dishka provider of the application."""

from dishka import Provider

from app.event_handlers import EventHandlersProvider
from core.infrastructure.provider import core_providers
from modules.projects.provider import ProjectsProvider


def get_providers() -> tuple[Provider, ...]:
    return (*core_providers(), EventHandlersProvider(), ProjectsProvider())
