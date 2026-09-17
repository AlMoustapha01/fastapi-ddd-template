"""Integration tests for create section endpoint."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from modules.rules.application.commands import (
    CreateSectionCommand,
    CreateSectionRequest,
)
from modules.rules.domain.entities.section import Section
from modules.rules.domain.exceptions import SectionAlreadyExistsError


@pytest.fixture
def mock_section_repository() -> AsyncMock:
    """Create a mock section repository."""
    repository = AsyncMock()
    repository.add = AsyncMock()
    return repository


@pytest.fixture
def mock_flusher() -> AsyncMock:
    """Create a mock flusher."""
    flusher = AsyncMock()
    flusher.flush = AsyncMock()
    return flusher


@pytest.fixture
def mock_transaction_manager() -> AsyncMock:
    """Create a mock transaction manager."""
    tx_manager = AsyncMock()
    tx_manager.commit = AsyncMock()
    return tx_manager


@pytest.fixture
def create_section_command(
    mock_section_repository: AsyncMock,
    mock_flusher: AsyncMock,
    mock_transaction_manager: AsyncMock,
) -> CreateSectionCommand:
    """Create a CreateSectionCommand with mocked dependencies."""
    return CreateSectionCommand(
        section_repository=mock_section_repository,
        flusher=mock_flusher,
        transaction_manager=mock_transaction_manager,
    )


class TestCreateSectionCommand:
    """Test CreateSectionCommand business logic."""

    @pytest.mark.asyncio
    async def test_execute_creates_section_successfully(
        self,
        create_section_command: CreateSectionCommand,
        mock_section_repository: AsyncMock,
        mock_flusher: AsyncMock,
        mock_transaction_manager: AsyncMock,
    ) -> None:
        """Test successful section creation."""
        # Arrange
        request = CreateSectionRequest(
            name="Introduction to Python",
            description="Learn Python basics",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        mock_section_repository.add.assert_called_once()
        mock_flusher.flush.assert_called_once()
        mock_transaction_manager.commit.assert_called_once()

        # Verify the section was created with correct properties
        added_section = mock_section_repository.add.call_args[0][0]
        assert isinstance(added_section, Section)
        assert added_section.props.name == "Introduction to Python"
        assert added_section.props.description == "Learn Python basics"

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_section_already_exists(
        self,
        create_section_command: CreateSectionCommand,
        mock_flusher: AsyncMock,
    ) -> None:
        """Test that SectionAlreadyExistsError is raised when slug exists."""
        # Arrange
        request = CreateSectionRequest(
            name="Existing Section",
            description="This section already exists",
        )
        mock_flusher.flush.side_effect = SectionAlreadyExistsError("existing-section")

        # Act & Assert
        with pytest.raises(SectionAlreadyExistsError):
            await create_section_command.execute(request)

    @pytest.mark.asyncio
    async def test_execute_creates_correct_slug(
        self,
        create_section_command: CreateSectionCommand,
        mock_section_repository: AsyncMock,
    ) -> None:
        """Test that the correct slug is generated from the name."""
        # Arrange
        request = CreateSectionRequest(
            name="Advanced Machine Learning",
            description="Deep dive into ML",
        )

        # Act
        await create_section_command.execute(request)

        # Assert
        added_section = mock_section_repository.add.call_args[0][0]
        assert added_section.props.slug.value == "advanced-machine-learning"

    @pytest.mark.asyncio
    async def test_execute_with_special_characters_in_name(
        self,
        create_section_command: CreateSectionCommand,
        mock_section_repository: AsyncMock,
    ) -> None:
        """Test section creation with special characters in name."""
        # Arrange
        request = CreateSectionRequest(
            name="C++ & Object-Oriented Programming",
            description="Learn C++ OOP",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        added_section = mock_section_repository.add.call_args[0][0]
        assert added_section.props.name == "C++ & Object-Oriented Programming"
        assert added_section.props.slug.value == "c-object-oriented-programming"


class TestCreateSectionRequestValidation:
    """Test request validation for create section."""

    @pytest.mark.asyncio
    async def test_request_with_valid_data(
        self,
        create_section_command: CreateSectionCommand,
    ) -> None:
        """Test that valid request data is accepted."""
        # Arrange
        request = CreateSectionRequest(
            name="Valid Section Name",
            description="Valid description",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        assert "id" in response
        assert isinstance(response["id"], UUID)

    @pytest.mark.asyncio
    async def test_request_with_unicode_characters(
        self,
        create_section_command: CreateSectionCommand,
    ) -> None:
        """Test request with unicode characters."""
        # Arrange
        request = CreateSectionRequest(
            name="Programmation en Français 🇫🇷",
            description="Apprendre à programmer",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        assert "id" in response
        assert isinstance(response["id"], UUID)


class TestCreateSectionIntegration:
    """Integration tests combining command and endpoint."""

    @pytest.mark.asyncio
    async def test_full_flow_from_request_to_response(
        self,
        create_section_command: CreateSectionCommand,
    ) -> None:
        """Test the complete flow from request to response."""
        # Arrange
        request = CreateSectionRequest(
            name="Full Integration Test",
            description="Testing the complete flow",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        assert "id" in response
        assert isinstance(response["id"], UUID)

    @pytest.mark.asyncio
    async def test_command_generates_valid_uuid7(
        self,
        create_section_command: CreateSectionCommand,
    ) -> None:
        """Test that command generates valid UUID7."""
        # Arrange
        request = CreateSectionRequest(
            name="UUID Test Section",
            description="Testing UUID generation",
        )

        # Act
        response = await create_section_command.execute(request)

        # Assert
        section_id = response["id"]
        # UUID7 has version 7 (0111 in binary = 7)
        assert section_id.version == 7

    @pytest.mark.asyncio
    async def test_multiple_sections_have_unique_ids(
        self,
        create_section_command: CreateSectionCommand,
    ) -> None:
        """Test that multiple sections get unique IDs."""
        # Arrange
        request1 = CreateSectionRequest(name="Section 1", description="First section")
        request2 = CreateSectionRequest(name="Section 2", description="Second section")

        # Act
        response1 = await create_section_command.execute(request1)
        response2 = await create_section_command.execute(request2)

        # Assert
        assert response1["id"] != response2["id"]
