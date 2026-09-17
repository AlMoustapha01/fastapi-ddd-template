"""Pytest configuration and shared fixtures."""

import pytest
import uuid_utils.compat as uuid_utils

from modules.rules.domain.entities.section import CreateSectionProps, Section
from modules.rules.domain.value_objects import SectionId, SlugValueObject


@pytest.fixture
def sample_section() -> Section:
    """Create a sample section for testing."""
    props = CreateSectionProps(
        name="Sample Section",
        description="This is a sample section for testing",
    )
    return Section.create(props)


@pytest.fixture
def inactive_section() -> Section:
    """Create an inactive section for testing."""
    section = Section.create(
        CreateSectionProps(
            name="Inactive Section",
            description="This section is inactive",
        )
    )
    section.make_inactive()
    return section


@pytest.fixture
def section_id() -> SectionId:
    """Generate a new section ID."""
    return SectionId(uuid_utils.uuid7())


@pytest.fixture
def sample_slug() -> SlugValueObject:
    """Create a sample slug."""
    return SlugValueObject.from_text("Sample Section")
