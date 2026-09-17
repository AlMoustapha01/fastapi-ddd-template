"""Unit tests for Rule entity."""

from datetime import UTC, datetime

import pytest
import uuid_utils.compat as uuid_utils

from modules.rules.domain.entities.rule import (
    CreateRuleProps,
    Rule,
    RuleProps,
)
from modules.rules.domain.enums import BalanceType, ProfileType, RuleStatus
from modules.rules.domain.value_objects import (
    RuleId,
    SectionId,
    SlugValueObject,
)
from modules.rules.domain.value_objects.rule_config import (
    RuleConfig,
    SelectClause,
    TableReference,
    WhereClause,
)
from modules.rules.domain.value_objects.rule_config.select_clause import SelectField


class TestRuleCreation:
    """Test Rule entity creation."""

    def test_create_rule_with_factory_method(self) -> None:
        """Test creating a rule using the factory method."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Transaction Rule",
            description="Rule for transaction processing",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        rule = Rule.create(props)

        # Assert
        assert rule.id_ is not None
        assert isinstance(rule.id_, RuleId)
        assert rule.props.name == "Transaction Rule"
        assert rule.props.description == "Rule for transaction processing"
        assert rule.props.database_table_name == ["transactions"]
        assert rule.props.balance_type == BalanceType.MAIN_BALANCE
        assert rule.props.profile_type == ProfileType.PREPAID
        assert rule.props.section_id == section_id
        assert rule.props.status == RuleStatus.DRAFT
        assert rule.props.slug == SlugValueObject.from_text("Transaction Rule")
        assert rule.created_at_ is not None
        assert rule.updated_at_ is not None

    def test_create_rule_with_constructor(self) -> None:
        """Test creating a rule using the constructor."""
        # Arrange
        rule_id = RuleId(uuid_utils.uuid7())
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("total")]),
            from_table=TableReference("orders"),
        )
        props = RuleProps(
            name="Order Rule",
            slug=SlugValueObject.from_text("Order Rule"),
            description="Rule for order processing",
            database_table_name=["orders"],
            config=config,
            balance_type=BalanceType.CRED,
            profile_type=ProfileType.HYBRID,
            section_id=section_id,
            status=RuleStatus.DRAFT,
        )
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

        # Act
        rule = Rule(
            id_=rule_id,
            props=props,
            created_at_=created_at,
            updated_at_=updated_at,
        )

        # Assert
        assert rule.id_ == rule_id
        assert rule.props.name == "Order Rule"
        assert rule.props.description == "Rule for order processing"
        assert rule.props.balance_type == BalanceType.CRED
        assert rule.props.profile_type == ProfileType.HYBRID
        assert rule.props.status == RuleStatus.DRAFT
        assert rule.created_at_ == created_at
        assert rule.updated_at_ == updated_at


class TestRuleValidation:
    """Test Rule entity validation."""

    def test_rule_name_cannot_be_empty(self) -> None:
        """Test that rule name cannot be empty."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            Rule.create(props)

    def test_rule_name_cannot_exceed_max_length(self) -> None:
        """Test that rule name cannot exceed maximum length."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        long_name = "A" * 256  # Exceeds MAX_NAME_LENGTH (255)
        props = CreateRuleProps(
            name=long_name,
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Rule name cannot exceed 255 characters"):
            Rule.create(props)

    def test_rule_config_cannot_be_none(self) -> None:
        """Test that rule config cannot be None."""
        # Arrange
        rule_id = RuleId(uuid_utils.uuid7())
        section_id = SectionId(uuid_utils.uuid7())
        props = RuleProps(
            name="Test Rule",
            slug=SlugValueObject.from_text("Test Rule"),
            description="Test rule",
            database_table_name=["transactions"],
            config=None,  # type: ignore
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
            status=RuleStatus.DRAFT,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Rule config cannot be None"):
            Rule(id_=rule_id, props=props)

    def test_prepaid_profile_must_have_main_balance(self) -> None:
        """Test that PREPAID profile can only have MAIN_BALANCE."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Invalid Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.CRED,  # Invalid for PREPAID
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="Prepaid profile can only have main balance"
        ):
            Rule.create(props)

    def test_hybrid_profile_can_have_any_balance_type(self) -> None:
        """Test that HYBRID profile can have any balance type."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )

        # Act & Assert - Should not raise
        for balance_type in [
            BalanceType.MAIN_BALANCE,
            BalanceType.CRED,
        ]:
            props = CreateRuleProps(
                name=f"Rule {balance_type.value}",
                description="Test rule",
                database_table_name=["transactions"],
                config=config,
                balance_type=balance_type,
                profile_type=ProfileType.HYBRID,
                section_id=section_id,
            )
            rule = Rule.create(props)
            assert rule.props.balance_type == balance_type

    def test_rule_config_must_be_valid(self) -> None:
        """Test that rule config must be valid."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        # Empty select clause - invalid config
        # SelectClause validates on init, so we test at RuleConfig level
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        # Manually set empty fields to bypass SelectClause validation
        config.select.fields = []
        props = CreateRuleProps(
            name="Invalid Config Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act & Assert
        with pytest.raises(
            ValueError, match="RuleConfig must have at least one select field"
        ):
            Rule.create(props)


class TestRuleStatusTransitions:
    """Test Rule status transitions."""

    def test_draft_can_transition_to_to_validate(self) -> None:
        """Test that DRAFT can transition to TO_VALIDATE."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)

        # Act
        rule.make_to_validate()

        # Assert
        assert rule.props.status == RuleStatus.TO_VALIDATE

    def test_to_validate_can_transition_to_in_production(self) -> None:
        """Test that TO_VALIDATE can transition to IN_PRODUCTION."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)
        rule.make_to_validate()

        # Act
        rule.make_in_production()

        # Assert
        assert rule.props.status == RuleStatus.IN_PRODUCTION

    def test_to_validate_can_transition_back_to_draft(self) -> None:
        """Test that TO_VALIDATE can transition back to DRAFT."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)
        rule.make_to_validate()

        # Act
        rule.make_draft()

        # Assert
        assert rule.props.status == RuleStatus.DRAFT

    def test_in_production_can_transition_to_archived(self) -> None:
        """Test that IN_PRODUCTION can transition to ARCHIVED."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)
        rule.make_to_validate()
        rule.make_in_production()

        # Act
        rule.make_archived()

        # Assert
        assert rule.props.status == RuleStatus.ARCHIVED

    def test_draft_cannot_transition_to_in_production(self) -> None:
        """Test that DRAFT cannot transition directly to IN_PRODUCTION."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid status transition from DRAFT to IN_PRODUCTION"
        ):
            rule.make_in_production()

    def test_in_production_cannot_transition_to_draft(self) -> None:
        """Test that IN_PRODUCTION cannot transition to DRAFT."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)
        rule.make_to_validate()
        rule.make_in_production()

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid status transition from IN_PRODUCTION to DRAFT"
        ):
            rule.make_draft()

    def test_archived_cannot_transition_to_any_status(self) -> None:
        """Test that ARCHIVED cannot transition to any other status."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Test Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )
        rule = Rule.create(props)
        rule.make_to_validate()
        rule.make_in_production()
        rule.make_archived()

        # Act & Assert
        with pytest.raises(
            ValueError, match="Invalid status transition from ARCHIVED to DRAFT"
        ):
            rule.make_draft()


class TestRuleSlugGeneration:
    """Test Rule slug generation."""

    def test_slug_is_generated_from_name(self) -> None:
        """Test that slug is automatically generated from name."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="My Transaction Rule",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        rule = Rule.create(props)

        # Assert
        assert rule.props.slug.value == "my-transaction-rule"

    def test_slug_handles_special_characters(self) -> None:
        """Test that slug properly handles special characters."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        props = CreateRuleProps(
            name="Rule #1: Data & Voice!",
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        rule = Rule.create(props)

        # Assert
        assert rule.props.slug.value == "rule-1-data-voice"

    def test_invalid_slug_raises_error(self) -> None:
        """Test that invalid slug raises error."""
        # Arrange
        rule_id = RuleId(uuid_utils.uuid7())
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([SelectField("amount")]),
            from_table=TableReference("transactions"),
        )
        # Create props with mismatched slug
        props = RuleProps(
            name="Test Rule",
            slug=SlugValueObject.from_text("different-slug"),
            description="Test rule",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
            status=RuleStatus.DRAFT,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Slug is not valid for the given name"):
            Rule(id_=rule_id, props=props)


class TestRuleConfigValidation:
    """Test Rule config validation."""

    def test_rule_with_valid_complex_config(self) -> None:
        """Test rule with valid complex configuration."""
        # Arrange
        section_id = SectionId(uuid_utils.uuid7())
        config = RuleConfig(
            select=SelectClause([
                SelectField("customer_id"),
                SelectField("SUM(amount)", alias="total"),
            ]),
            from_table=TableReference("transactions", alias="t"),
            where=WhereClause.from_dict({
                "conditions": [
                    {
                        "field": "status",
                        "operator": "=",
                        "value": "COMPLETED",
                    }
                ],
                "logical_operator": "AND",
            }),
            group_by=["customer_id"],
            order_by=["total DESC"],
        )
        props = CreateRuleProps(
            name="Complex Rule",
            description="Rule with complex config",
            database_table_name=["transactions"],
            config=config,
            balance_type=BalanceType.MAIN_BALANCE,
            profile_type=ProfileType.PREPAID,
            section_id=section_id,
        )

        # Act
        rule = Rule.create(props)

        # Assert
        assert rule.props.config == config
        assert len(rule.props.config.select.fields) == 2
        assert rule.props.config.from_table.alias == "t"
        assert rule.props.config.group_by == ["customer_id"]
