"""Dishka providers of the shared kernel."""

from dishka import Provider, Scope, from_context, provide

from core.application.event_bus import EventBus
from core.infrastructure.db.provider import DatabaseProvider
from core.infrastructure.events.in_process_bus import InProcessEventBus
from core.infrastructure.settings import DatabaseSettings, Settings


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide
    def database_settings(self, settings: Settings) -> DatabaseSettings:
        return settings.database


class EventsProvider(Provider):
    event_bus = provide(InProcessEventBus, scope=Scope.REQUEST, provides=EventBus)


def core_providers() -> tuple[Provider, ...]:
    return (SettingsProvider(), DatabaseProvider(), EventsProvider())
