from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from .common import SqlExpression


class ComparisonOperator(Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE = "LIKE"
    NOT_LIKE = "NOT LIKE"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class LogicalOperator(Enum):
    AND = "AND"
    OR = "OR"


BTW_LEN = 2


# -------------------------------
# WHERE Condition
# -------------------------------
# ============================================================
# WHERE
# ============================================================
@dataclass(frozen=True)
class WhereCondition:
    field: str | SqlExpression
    operator: ComparisonOperator
    value: str | int | float | bool | list[Any] | datetime | date | None

    def __post_init__(self):
        if isinstance(self.field, str) and not re.match(
            r"^[a-zA-Z_][a-zA-Z0-9_.]*$", self.field
        ):
            raise ValueError(f"Invalid field name: {self.field}")

        if (
            self.operator
            in {ComparisonOperator.IS_NULL, ComparisonOperator.IS_NOT_NULL}
            and self.value is not None
        ):
            raise ValueError(f"{self.operator.value} cannot have a value")

        if self.operator in {
            ComparisonOperator.IN,
            ComparisonOperator.NOT_IN,
        } and not isinstance(self.value, list):
            raise ValueError(f"{self.operator.value} requires a list")

        if self.operator is ComparisonOperator.BETWEEN:
            if not isinstance(self.value, list) or len(self.value) != BTW_LEN:
                raise ValueError("BETWEEN requires exactly 2 values")
            if not isinstance(self.value[0], type(self.value[1])):
                raise ValueError("BETWEEN values must have the same type")

    def _format_value(self, val: Any) -> str:
        result: str

        if val is None:
            result = "NULL"
        elif isinstance(val, bool):
            result = "TRUE" if val else "FALSE"
        elif isinstance(val, (int, float)):
            result = str(val)
        elif isinstance(val, str):
            safe = val.replace("'", "''")
            result = f"'{safe}'"
        elif isinstance(val, datetime):
            result = f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif isinstance(val, date):
            result = f"'{val.strftime('%Y-%m-%d')}'"
        elif isinstance(val, SqlExpression):
            result = val.to_sql()
        else:
            raise ValueError(f"Unsupported value type: {type(val)}")

        return result

    def to_sql(self) -> str:
        field_sql = (
            self.field.to_sql() if isinstance(self.field, SqlExpression) else self.field
        )
        if self.operator in {
            ComparisonOperator.IS_NULL,
            ComparisonOperator.IS_NOT_NULL,
        }:
            return f"{field_sql} {self.operator.value}"
        if self.operator in {ComparisonOperator.IN, ComparisonOperator.NOT_IN}:
            # Type narrowing: at this point we know self.value is a list
            if not isinstance(self.value, list):
                msg = f"{self.operator.value} requires a list value"
                raise TypeError(msg)
            values_str = ", ".join(self._format_value(v) for v in self.value)
            return f"{field_sql} {self.operator.value} ({values_str})"
        if self.operator == ComparisonOperator.BETWEEN:
            # Type narrowing: at this point we know self.value is a list with 2 items
            if not isinstance(self.value, list):
                msg = "BETWEEN requires a list value"
                raise TypeError(msg)
            if len(self.value) != BTW_LEN:
                msg = f"BETWEEN requires exactly {BTW_LEN} values"
                raise ValueError(msg)
            v1, v2 = self.value
            formatted_v1 = self._format_value(v1)
            formatted_v2 = self._format_value(v2)
            return f"{field_sql} BETWEEN {formatted_v1} AND {formatted_v2}"
        return f"{field_sql} {self.operator.value} {self._format_value(self.value)}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field.to_dict()
            if isinstance(self.field, SqlExpression)
            else self.field,
            "operator": self.operator.value,
            "value": (
                [v.to_dict() if isinstance(v, SqlExpression) else v for v in self.value]
                if isinstance(self.value, list)
                else self.value.to_dict()
                if isinstance(self.value, SqlExpression)
                else self.value
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WhereCondition:
        field: str | SqlExpression = data["field"]
        if isinstance(field, dict) and (
            ("function" in field and "args" in field)
            or ("expression" in field and "params" in field)
        ):
            field = SqlExpression.from_dict(field)

        value: str | int | float | bool | list[Any] | datetime | date | None
        value = data.get("value")
        if isinstance(value, dict) and (
            ("function" in value and "args" in value)
            or ("expression" in value and "params" in value)
        ):
            value = SqlExpression.from_dict(value)  # type: ignore[assignment]
        elif isinstance(value, list):
            value = [
                SqlExpression.from_dict(v)
                if isinstance(v, dict)
                and (
                    ("function" in v and "args" in v)
                    or ("expression" in v and "params" in v)
                )
                else v
                for v in value
            ]

        return cls(
            field=field, operator=ComparisonOperator(data["operator"]), value=value
        )


@dataclass(frozen=True)
class WhereClause:
    conditions: list[WhereCondition | WhereClause]
    logical_operator: LogicalOperator = LogicalOperator.AND

    def __post_init__(self):
        if not self.conditions:
            raise ValueError("WhereClause must have at least one condition")
        if len(self.conditions) > 1 and not self.logical_operator:
            raise ValueError("Logical operator required for multiple conditions")

    def to_sql(self) -> str:
        if len(self.conditions) == 1:
            return self.conditions[0].to_sql()
        parts = [
            f"({c.to_sql()})"
            if isinstance(c, WhereClause) and len(c.conditions) > 1
            else c.to_sql()
            for c in self.conditions
        ]
        return f" {self.logical_operator.value} ".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "logical_operator": self.logical_operator.value,
            "conditions": [c.to_dict() for c in self.conditions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WhereClause:
        conditions: list[WhereCondition | WhereClause] = []
        for c in data["conditions"]:
            if "operator" in c:  # WhereCondition
                conditions.append(WhereCondition.from_dict(c))
            else:  # nested WhereClause
                conditions.append(WhereClause.from_dict(c))
        return cls(
            conditions=conditions,
            logical_operator=LogicalOperator(data["logical_operator"]),
        )
