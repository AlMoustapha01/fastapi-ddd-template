"""Logging configuration is idempotent and keeps existing handlers."""

import logging
from collections.abc import Iterator

import pytest

from core.infrastructure.logs import HANDLER_NAME, configure_logging
from core.infrastructure.settings import LogLevel


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    level, handlers = root.level, list(root.handlers)
    yield
    root.setLevel(level)
    root.handlers[:] = handlers


def test_sets_level_and_installs_a_single_handler() -> None:
    configure_logging(LogLevel.DEBUG)
    configure_logging(LogLevel.WARNING)

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert [handler.get_name() for handler in root.handlers].count(HANDLER_NAME) == 1


def test_keeps_handlers_installed_by_others() -> None:
    other = logging.NullHandler()
    logging.getLogger().addHandler(other)

    configure_logging(LogLevel.INFO)

    assert other in logging.getLogger().handlers
