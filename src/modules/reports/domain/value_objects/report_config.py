"""ReportConfig value object."""

from dataclasses import dataclass
from typing import TypedDict

from core.lib.base.value_object import ValueObject

from .rule_id import RuleId, RuleIdList


class ReportConfigProps(TypedDict):
    """Properties for ReportConfig."""

    initial_credit_rule_id: str
    final_credit_rule_id: str
    recharge_rules_ids: list[str]
    consumption_rules_ids: list[str]


@dataclass(frozen=True, slots=True, repr=False)
class ReportConfig(ValueObject):
    """Value object representing a Report configuration."""

    _initial_credit_rule_id: RuleId
    _final_credit_rule_id: RuleId
    _recharge_rules_ids: RuleIdList
    _consumption_rules_ids: RuleIdList

    def __init__(self, props: ReportConfigProps) -> None:
        """Initialize ReportConfig from props."""
        initial_credit = RuleId(props["initial_credit_rule_id"])
        final_credit = RuleId(props["final_credit_rule_id"])
        recharge_rules = RuleIdList(props["recharge_rules_ids"])
        consumption_rules = RuleIdList(props["consumption_rules_ids"])

        object.__setattr__(self, "_initial_credit_rule_id", initial_credit)
        object.__setattr__(self, "_final_credit_rule_id", final_credit)
        object.__setattr__(self, "_recharge_rules_ids", recharge_rules)
        object.__setattr__(self, "_consumption_rules_ids", consumption_rules)

        self._validate()

    def _validate(self) -> None:
        """Validate business rules for the configuration."""
        if self._recharge_rules_ids.is_empty():
            raise ValueError("At least one recharge rule is required")

        if self._consumption_rules_ids.is_empty():
            raise ValueError("At least one consumption rule is required")

        # Ensure no duplicate rules across different categories
        all_rule_ids = [
            self._initial_credit_rule_id,
            self._final_credit_rule_id,
            *self._recharge_rules_ids.values,
            *self._consumption_rules_ids.values,
        ]

        unique_rule_ids = {rid.value for rid in all_rule_ids}
        if len(unique_rule_ids) != len(all_rule_ids):
            raise ValueError("Duplicate rule IDs found across different categories")

    @property
    def initial_credit_rule_id(self) -> RuleId:
        """Return the initial credit rule ID."""
        return self._initial_credit_rule_id

    @property
    def final_credit_rule_id(self) -> RuleId:
        """Return the final credit rule ID."""
        return self._final_credit_rule_id

    @property
    def recharge_rules_ids(self) -> RuleIdList:
        """Return the recharge rules IDs."""
        return self._recharge_rules_ids

    @property
    def consumption_rules_ids(self) -> RuleIdList:
        """Return the consumption rules IDs."""
        return self._consumption_rules_ids

    def to_plain_object(self) -> ReportConfigProps:
        """Convert to plain dictionary for serialization."""
        return ReportConfigProps(
            initial_credit_rule_id=self._initial_credit_rule_id.value,
            final_credit_rule_id=self._final_credit_rule_id.value,
            recharge_rules_ids=self._recharge_rules_ids.string_values,
            consumption_rules_ids=self._consumption_rules_ids.string_values,
        )

    def with_initial_credit_rule(self, rule_id: str) -> "ReportConfig":
        """Return new config with updated initial credit rule."""
        props = self.to_plain_object()
        props["initial_credit_rule_id"] = rule_id
        return ReportConfig(props)

    def with_final_credit_rule(self, rule_id: str) -> "ReportConfig":
        """Return new config with updated final credit rule."""
        props = self.to_plain_object()
        props["final_credit_rule_id"] = rule_id
        return ReportConfig(props)

    def with_recharge_rules(self, rule_ids: list[str]) -> "ReportConfig":
        """Return new config with updated recharge rules."""
        props = self.to_plain_object()
        props["recharge_rules_ids"] = rule_ids
        return ReportConfig(props)

    def with_consumption_rules(self, rule_ids: list[str]) -> "ReportConfig":
        """Return new config with updated consumption rules."""
        props = self.to_plain_object()
        props["consumption_rules_ids"] = rule_ids
        return ReportConfig(props)

    def add_recharge_rule(self, rule_id: str) -> "ReportConfig":
        """Add a recharge rule to the config."""
        new_recharge_rules = self._recharge_rules_ids.add(RuleId(rule_id))
        props = self.to_plain_object()
        props["recharge_rules_ids"] = new_recharge_rules.string_values
        return ReportConfig(props)

    def remove_recharge_rule(self, rule_id: str) -> "ReportConfig":
        """Remove a recharge rule from the config."""
        new_recharge_rules = self._recharge_rules_ids.remove(RuleId(rule_id))
        props = self.to_plain_object()
        props["recharge_rules_ids"] = new_recharge_rules.string_values
        return ReportConfig(props)

    def add_consumption_rule(self, rule_id: str) -> "ReportConfig":
        """Add a consumption rule to the config."""
        new_consumption_rules = self._consumption_rules_ids.add(RuleId(rule_id))
        props = self.to_plain_object()
        props["consumption_rules_ids"] = new_consumption_rules.string_values
        return ReportConfig(props)

    def remove_consumption_rule(self, rule_id: str) -> "ReportConfig":
        """Remove a consumption rule from the config."""
        new_consumption_rules = self._consumption_rules_ids.remove(RuleId(rule_id))
        props = self.to_plain_object()
        props["consumption_rules_ids"] = new_consumption_rules.string_values
        return ReportConfig(props)

    @property
    def total_rules_count(self) -> int:
        """Return the total number of rules configured."""
        return 2 + self._recharge_rules_ids.length + self._consumption_rules_ids.length

    def is_complete(self) -> bool:
        """Check if the configuration is complete."""
        return (
            len(self._initial_credit_rule_id.value) > 0
            and len(self._final_credit_rule_id.value) > 0
            and not self._recharge_rules_ids.is_empty()
            and not self._consumption_rules_ids.is_empty()
        )
