"""Synchronous in-process event bus backed by the Dishka request container."""

import logging

from dishka import AsyncContainer

from core.application.event_bus import EventBus, EventHandlerRegistry
from core.domain.events import DomainEvent

log = logging.getLogger(__name__)


class InProcessEventBus(EventBus):
    """Resolve each registered handler from the current scope and await it in order."""

    def __init__(
        self, container: AsyncContainer, registry: EventHandlerRegistry
    ) -> None:
        self._container = container
        self._registry = registry

    async def publish(self, event: DomainEvent) -> None:
        for handler_type in self._registry.handlers_for(event):
            handler = await self._container.get(handler_type)
            log.debug(
                "Dispatching %s to %s", type(event).__name__, handler_type.__name__
            )
            await handler.handle(event)
