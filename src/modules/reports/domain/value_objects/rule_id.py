"""RuleId and RuleIdList value objects for report configuration."""

from dataclasses import dataclass, field

from core.lib.base.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class RuleId(ValueObject):
    """Value object representing a Rule ID reference."""

    value: str

    def __post_init__(self) -> None:
        """Validate rule ID constraints."""
        if not self.value or not self.value.strip():
            raise ValueError("Rule ID cannot be empty")
        # Ensure the value is trimmed
        object.__setattr__(self, "value", self.value.strip())

    def equals(self, other: "RuleId") -> bool:
        """Check equality with another RuleId."""
        return self.value == other.value


@dataclass(frozen=True, slots=True, repr=False)
class RuleIdList(ValueObject):
    """Value object representing a list of Rule IDs."""

    _values: tuple[RuleId, ...] = field(default_factory=tuple)

    def __init__(self, values: list[str]) -> None:
        """Initialize with a list of string values."""
        if not isinstance(values, list):
            raise ValueError("Rule IDs must be a list")
        rule_ids = tuple(RuleId(value) for value in values)
        object.__setattr__(self, "_values", rule_ids)

    @property
    def values(self) -> list[RuleId]:
        """Return a copy of the rule IDs."""
        return list(self._values)

    @property
    def string_values(self) -> list[str]:
        """Return the string values of the rule IDs."""
        return [rule_id.value for rule_id in self._values]

    @property
    def length(self) -> int:
        """Return the number of rule IDs."""
        return len(self._values)

    def is_empty(self) -> bool:
        """Check if the list is empty."""
        return len(self._values) == 0

    def contains(self, rule_id: RuleId) -> bool:
        """Check if the list contains a rule ID."""
        return any(rid.equals(rule_id) for rid in self._values)

    def add(self, rule_id: RuleId) -> "RuleIdList":
        """Add a rule ID to the list (returns new instance)."""
        if self.contains(rule_id):
            raise ValueError(f"Rule ID {rule_id.value} already exists in the list")
        return RuleIdList([*self.string_values, rule_id.value])

    def remove(self, rule_id: RuleId) -> "RuleIdList":
        """Remove a rule ID from the list (returns new instance)."""
        filtered_values = [rid.value for rid in self._values if not rid.equals(rule_id)]
        if len(filtered_values) == len(self._values):
            raise ValueError(f"Rule ID {rule_id.value} not found in the list")
        return RuleIdList(filtered_values)
