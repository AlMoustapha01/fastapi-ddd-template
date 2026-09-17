"""Unit tests for Section entity."""

from datetime import UTC, datetime

import pytest
import uuid_utils.compat as uuid_utils

from modules.rules.domain.entities.section import (
    CreateSectionProps,
    Section,
    SectionProps,
)
from modules.rules.domain.enums import SectionStatus
from modules.rules.domain.value_objects import SectionId, SlugValueObject


class TestSectionCreation:
    """Test Section entity creation."""

    def test_create_section_with_factory_method(self) -> None:
        """Test creating a section using the factory method."""
        # Arrange
        props = CreateSectionProps(
            name="Introduction to Python",
            description="Learn the basics of Python programming",
        )

        # Act
        section = Section.create(props)

        # Assert
        assert section.id_ is not None
        assert isinstance(section.id_, SectionId)
        assert section.props.name == "Introduction to Python"
        assert section.props.description == "Learn the basics of Python programming"
        assert section.props.status == SectionStatus.ACTIVE
        assert section.props.slug == SlugValueObject.from_text("Introduction to Python")
        assert section.created_at_ is not None
        assert section.updated_at_ is not None

    def test_create_section_with_constructor(self) -> None:
        """Test creating a section using the constructor."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        props = SectionProps(
            name="Advanced Python",
            slug=SlugValueObject.from_text("Advanced Python"),
            description="Deep dive into Python",
            status=SectionStatus.ACTIVE,
        )
        created_at = datetime.now(tz=UTC)
        updated_at = datetime.now(tz=UTC)

        # Act
        section = Section(
            id_=section_id,
            props=props,
            created_at_=created_at,
            updated_at_=updated_at,
        )

        # Assert
        assert section.id_ == section_id
        assert section.props.name == "Advanced Python"
        assert section.props.description == "Deep dive into Python"
        assert section.props.status == SectionStatus.ACTIVE
        assert section.created_at_ == created_at
        assert section.updated_at_ == updated_at

    def test_create_section_generates_correct_slug(self) -> None:
        """Test that section creation generates the correct slug."""
        # Arrange
        props = CreateSectionProps(
            name="Machine Learning Basics",
            description="Introduction to ML",
        )

        # Act
        section = Section.create(props)

        # Assert
        expected_slug = SlugValueObject.from_text("Machine Learning Basics")
        assert section.props.slug == expected_slug

    def test_create_section_with_special_characters_in_name(self) -> None:
        """Test creating a section with special characters in name."""
        # Arrange
        props = CreateSectionProps(
            name="C++ & Object-Oriented Programming",
            description="Learn C++ OOP concepts",
        )

        # Act
        section = Section.create(props)

        # Assert
        assert section.props.name == "C++ & Object-Oriented Programming"
        assert section.props.slug.value == "c-object-oriented-programming"


class TestSectionStatusManagement:
    """Test Section status management methods."""

    def test_make_inactive_changes_status(self) -> None:
        """Test that make_inactive changes status to INACTIVE."""
        # Arrange
        props = CreateSectionProps(
            name="Test Section",
            description="Test description",
        )
        section = Section.create(props)
        assert section.props.status == SectionStatus.ACTIVE

        # Act
        section.make_inactive()

        # Assert
        assert section.props.status == SectionStatus.INACTIVE

    def test_make_active_changes_status(self) -> None:
        """Test that make_active changes status to ACTIVE."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        props = SectionProps(
            name="Test Section",
            slug=SlugValueObject.from_text("Test Section"),
            description="Test description",
            status=SectionStatus.INACTIVE,
        )
        section = Section(id_=section_id, props=props)
        assert section.props.status == SectionStatus.INACTIVE

        # Act
        section.make_active()

        # Assert
        assert section.props.status == SectionStatus.ACTIVE

    def test_make_inactive_when_already_inactive(self) -> None:
        """Test that make_inactive works when already inactive."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        props = SectionProps(
            name="Test Section",
            slug=SlugValueObject.from_text("Test Section"),
            description="Test description",
            status=SectionStatus.INACTIVE,
        )
        section = Section(id_=section_id, props=props)

        # Act
        section.make_inactive()

        # Assert
        assert section.props.status == SectionStatus.INACTIVE

    def test_make_active_when_already_active(self) -> None:
        """Test that make_active works when already active."""
        # Arrange
        props = CreateSectionProps(
            name="Test Section",
            description="Test description",
        )
        section = Section.create(props)

        # Act
        section.make_active()

        # Assert
        assert section.props.status == SectionStatus.ACTIVE

    def test_toggle_status_multiple_times(self) -> None:
        """Test toggling status multiple times."""
        # Arrange
        props = CreateSectionProps(
            name="Test Section",
            description="Test description",
        )
        section = Section.create(props)

        # Act & Assert
        assert section.props.status == SectionStatus.ACTIVE

        section.make_inactive()
        assert section.props.status == SectionStatus.INACTIVE

        section.make_active()
        assert section.props.status == SectionStatus.ACTIVE

        section.make_inactive()
        assert section.props.status == SectionStatus.INACTIVE


class TestSectionValidation:
    """Test Section validation methods."""

    def test_validate_with_valid_slug(self) -> None:
        """Test validation passes with valid slug."""
        # Arrange
        props = CreateSectionProps(
            name="Valid Section",
            description="Valid description",
        )

        # Act & Assert - Should not raise
        section = Section.create(props)
        section.validate()

    def test_validate_raises_error_with_empty_slug(self) -> None:
        """Test validation fails with empty slug."""
        # Act & Assert - SlugValueObject validates on creation
        with pytest.raises(ValueError, match="Slug cannot be empty"):
            SlugValueObject("")

    def test_validate_raises_error_with_mismatched_slug(self) -> None:
        """Test validation fails when slug doesn't match name."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        props = SectionProps(
            name="Test Section",
            slug=SlugValueObject("wrong-slug"),  # Doesn't match name
            description="Test description",
            status=SectionStatus.ACTIVE,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Slug is not valid"):
            Section(id_=section_id, props=props)


class TestSectionProperties:
    """Test Section properties and attributes."""

    def test_section_has_unique_id(self) -> None:
        """Test that each section has a unique ID."""
        # Arrange & Act
        section1 = Section.create(
            CreateSectionProps(name="Section 1", description="Description 1")
        )
        section2 = Section.create(
            CreateSectionProps(name="Section 2", description="Description 2")
        )

        # Assert
        assert section1.id_ != section2.id_

    def test_section_timestamps_are_set(self) -> None:
        """Test that timestamps are automatically set."""
        # Arrange
        before = datetime.now(tz=UTC)

        # Act
        section = Section.create(
            CreateSectionProps(name="Test Section", description="Test description")
        )

        # Assert
        after = datetime.now(tz=UTC)
        assert before <= section.created_at_ <= after
        assert before <= section.updated_at_ <= after

    def test_section_preserves_custom_timestamps(self) -> None:
        """Test that custom timestamps are preserved."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        custom_created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        custom_updated = datetime(2024, 1, 2, 12, 0, 0, tzinfo=UTC)
        props = SectionProps(
            name="Test Section",
            slug=SlugValueObject.from_text("Test Section"),
            description="Test description",
            status=SectionStatus.ACTIVE,
        )

        # Act
        section = Section(
            id_=section_id,
            props=props,
            created_at_=custom_created,
            updated_at_=custom_updated,
        )

        # Assert
        assert section.created_at_ == custom_created
        assert section.updated_at_ == custom_updated

    def test_section_props_are_accessible(self) -> None:
        """Test that all section properties are accessible."""
        # Arrange
        props = CreateSectionProps(
            name="Accessible Section",
            description="Testing property access",
        )

        # Act
        section = Section.create(props)

        # Assert
        assert section.props.name == "Accessible Section"
        assert section.props.description == "Testing property access"
        assert section.props.status == SectionStatus.ACTIVE
        assert isinstance(section.props.slug, SlugValueObject)


class TestSectionEdgeCases:
    """Test Section edge cases and boundary conditions."""

    def test_create_section_with_very_long_name(self) -> None:
        """Test that creating a section with a very long name fails."""
        # Arrange
        long_name = "A" * 500  # Exceeds MAX_NAME_LENGTH (255)
        props = CreateSectionProps(
            name=long_name,
            description="Test description",
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Section name cannot exceed 255 characters"
        ):
            Section.create(props)

    def test_create_section_with_max_length_name(self) -> None:
        """Test creating a section with maximum allowed name length."""
        # Arrange
        max_length_name = "A" * 255  # Exactly MAX_NAME_LENGTH
        props = CreateSectionProps(
            name=max_length_name,
            description="Test description",
        )

        # Act
        section = Section.create(props)

        # Assert
        assert section.props.name == max_length_name
        assert len(section.props.slug.value) > 0

    def test_create_section_with_empty_description(self) -> None:
        """Test that creating a section with empty description fails."""
        # Arrange
        props = CreateSectionProps(
            name="Test Section",
            description="",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Section description cannot be empty"):
            Section.create(props)

    def test_create_section_with_whitespace_only_description(self) -> None:
        """Test that creating a section with whitespace-only description fails."""
        # Arrange
        props = CreateSectionProps(
            name="Test Section",
            description="   ",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Section description cannot be empty"):
            Section.create(props)

    def test_create_section_with_unicode_characters(self) -> None:
        """Test creating a section with unicode characters."""
        # Arrange
        props = CreateSectionProps(
            name="Programmation en Français 🇫🇷",
            description="Apprendre à programmer",
        )

        # Act
        section = Section.create(props)

        # Assert
        assert section.props.name == "Programmation en Français 🇫🇷"
        assert section.props.description == "Apprendre à programmer"
