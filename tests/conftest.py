"""Shared pytest configuration."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test located under `tests/integration/` with `integration`."""
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)
