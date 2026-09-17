"""Integration tests for create rule endpoint."""

from unittest.mock import AsyncMock
from uuid import UUID

import pytest
import uuid_utils.compat as uuid_utils

from modules.rules.application.commands import (
    CreateRuleCommand,
    CreateRuleRequest,
)
from modules.rules.domain.entities.rule import Rule
from modules.rules.domain.enums import BalanceType, ProfileType
from modules.rules.domain.exceptions import RuleAlreadyExistsError


@pytest.fixture
def mock_rule_repository() -> AsyncMock:
    """Create a mock rule repository."""
    repository = AsyncMock()
    repository.add = AsyncMock()
    repository.find_one_by_slug = AsyncMock(return_value=None)
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
def create_rule_command(
    mock_rule_repository: AsyncMock,
    mock_flusher: AsyncMock,
    mock_transaction_manager: AsyncMock,
) -> CreateRuleCommand:
    """Create a CreateRuleCommand with mocked dependencies."""
    return CreateRuleCommand(
        rule_repository=mock_rule_repository,
        flusher=mock_flusher,
        transaction_manager=mock_transaction_manager,
    )


@pytest.fixture
def valid_rule_config() -> dict:
    """Create a valid rule configuration."""
    return {
        "select": {
            "fields": [
                {"expression": "customer_id", "alias": None},
                {"expression": "SUM(amount)", "alias": "total_amount"},
            ]
        },
        "from_table": {"name": "transactions", "alias": "t"},
        "joins": [],
        "where": {
            "conditions": [{"field": "status", "operator": "=", "value": "COMPLETED"}],
            "logical_operator": "AND",
        },
        "group_by": ["customer_id"],
        "having": [],
        "order_by": ["total_amount DESC"],
    }


class TestCreateRuleCommand:
    """Test CreateRuleCommand business logic."""

    @pytest.mark.asyncio
    async def test_execute_creates_rule_successfully(
        self,
        create_rule_command: CreateRuleCommand,
        mock_rule_repository: AsyncMock,
        mock_flusher: AsyncMock,
        mock_transaction_manager: AsyncMock,
        valid_rule_config: dict,
    ) -> None:
        """Test successful rule creation."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="Transaction Rule",
            description="Rule for transaction processing",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        response = await create_rule_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        mock_rule_repository.add.assert_called_once()
        mock_flusher.flush.assert_called_once()
        mock_transaction_manager.commit.assert_called_once()

        # Verify the rule was created with correct properties
        added_rule = mock_rule_repository.add.call_args[0][0]
        assert isinstance(added_rule, Rule)
        assert added_rule.props.name == "Transaction Rule"
        assert added_rule.props.description == "Rule for transaction processing"
        assert added_rule.props.database_table_name == ["transactions"]
        assert added_rule.props.balance_type == BalanceType.MAIN_BALANCE
        assert added_rule.props.profile_type == ProfileType.PREPAID
        assert added_rule.props.section_id.value == section_id

    @pytest.mark.asyncio
    async def test_execute_raises_error_when_rule_already_exists(
        self,
        create_rule_command: CreateRuleCommand,
        mock_flusher: AsyncMock,
        valid_rule_config: dict,
    ) -> None:
        """Test that RuleAlreadyExistsError is raised when slug exists."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="Existing Rule",
            description="This rule already exists",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        mock_flusher.flush.side_effect = RuleAlreadyExistsError("existing-rule")

        # Act & Assert
        with pytest.raises(RuleAlreadyExistsError, match="existing-rule"):
            await create_rule_command.execute(request)

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_invalid_name(
        self,
        create_rule_command: CreateRuleCommand,
        valid_rule_config: dict,
    ) -> None:
        """Test that RuleValidationError is raised for empty name."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="",  # Empty name
            description="Test rule",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await create_rule_command.execute(request)

    @pytest.mark.asyncio
    async def test_execute_raises_error_for_prepaid_with_non_main_balance(
        self,
        create_rule_command: CreateRuleCommand,
        valid_rule_config: dict,
    ) -> None:
        """Test that validation error is raised for PREPAID with non-MAIN_BALANCE."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="Invalid Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.CRED,  # Invalid for PREPAID
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Prepaid profile can only have main balance"
        ):
            await create_rule_command.execute(request)

    @pytest.mark.asyncio
    async def test_execute_creates_rule_with_minimal_config(
        self,
        create_rule_command: CreateRuleCommand,
        mock_rule_repository: AsyncMock,
        mock_flusher: AsyncMock,
        mock_transaction_manager: AsyncMock,
    ) -> None:
        """Test rule creation with minimal configuration (no where clause)."""
        # Arrange
        section_id = uuid_utils.uuid7()
        minimal_config = {
            "select": {"fields": [{"expression": "amount", "alias": None}]},
            "from_table": {"name": "transactions", "alias": None},
            "joins": [],
            "where": None,  # No where clause
            "group_by": [],
            "having": [],
            "order_by": [],
        }
        request = CreateRuleRequest(
            name="Minimal Rule",
            description="Rule with minimal config",
            database_table_name=["transactions"],
            config=minimal_config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        response = await create_rule_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        mock_rule_repository.add.assert_called_once()
        mock_flusher.flush.assert_called_once()
        mock_transaction_manager.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_creates_rule_with_hybrid_profile(
        self,
        create_rule_command: CreateRuleCommand,
        mock_rule_repository: AsyncMock,
        valid_rule_config: dict,
    ) -> None:
        """Test rule creation with HYBRID profile and CRED balance."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="Hybrid Rule",
            description="Rule for hybrid profile",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.CRED,
            profile_type=ProfileType.HYBRID,
            section_id=section_id,
        )

        # Act
        response = await create_rule_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        added_rule = mock_rule_repository.add.call_args[0][0]
        assert added_rule.props.profile_type == ProfileType.HYBRID
        assert added_rule.props.balance_type == BalanceType.CRED

    @pytest.mark.asyncio
    async def test_execute_creates_rule_with_multiple_tables(
        self,
        create_rule_command: CreateRuleCommand,
        mock_rule_repository: AsyncMock,
    ) -> None:
        """Test rule creation with multiple database tables."""
        # Arrange
        section_id = uuid_utils.uuid7()
        config_with_joins = {
            "select": {
                "fields": [
                    {"expression": "t.amount", "alias": None},
                    {"expression": "c.name", "alias": "customer_name"},
                ]
            },
            "from_table": {"name": "transactions", "alias": "t"},
            "joins": [
                {
                    "type": "INNER",
                    "table": "customers",
                    "alias": "c",
                    "on": "t.customer_id = c.id",
                }
            ],
            "where": None,
            "group_by": [],
            "having": [],
            "order_by": [],
        }
        request = CreateRuleRequest(
            name="Multi-Table Rule",
            description="Rule with multiple tables",
            database_table_name=["transactions", "customers"],
            config=config_with_joins,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        response = await create_rule_command.execute(request)

        # Assert
        assert isinstance(response["id"], UUID)
        added_rule = mock_rule_repository.add.call_args[0][0]
        assert added_rule.props.database_table_name == ["transactions", "customers"]
        assert len(added_rule.props.config.joins) == 1

    @pytest.mark.asyncio
    async def test_execute_rollback_on_flush_error(
        self,
        create_rule_command: CreateRuleCommand,
        mock_flusher: AsyncMock,
        mock_transaction_manager: AsyncMock,
        valid_rule_config: dict,
    ) -> None:
        """Test that transaction is rolled back on flush error."""
        # Arrange
        section_id = uuid_utils.uuid7()
        request = CreateRuleRequest(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=valid_rule_config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        mock_flusher.flush.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await create_rule_command.execute(request)

        # Verify commit was not called
        mock_transaction_manager.commit.assert_not_called()
