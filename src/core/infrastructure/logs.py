"""Logging configuration."""

import logging
from typing import Final

from core.infrastructure.settings import LogLevel

HANDLER_NAME: Final[str] = "app-console"
LOG_FORMAT: Final[str] = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"


def configure_logging(level: LogLevel) -> None:
    """Install the console handler once; later calls only update the root level."""
    root = logging.getLogger()
    root.setLevel(level.value)
    if any(handler.get_name() == HANDLER_NAME for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
