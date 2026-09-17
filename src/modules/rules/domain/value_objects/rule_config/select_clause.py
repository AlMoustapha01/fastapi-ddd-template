from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .common import SqlExpression


# ============================================================
# SELECT
# ============================================================
@dataclass(frozen=True)
class SelectField:
    expression: str | SqlExpression
    alias: str | None = None

    def __post_init__(self):
        if isinstance(self.expression, str) and not self.expression.strip():
            raise ValueError("SelectField expression cannot be empty")
        if self.alias and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.alias):
            raise ValueError(f"Invalid alias: {self.alias}")

    def to_sql(self) -> str:
        sql = (
            self.expression.to_sql()
            if isinstance(self.expression, SqlExpression)
            else self.expression
        )
        return f"{sql} AS {self.alias}" if self.alias else sql

    def to_dict(self) -> dict[str, Any]:
        return {
            "expression": self.expression.to_dict()
            if isinstance(self.expression, SqlExpression)
            else self.expression,
            "alias": self.alias,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SelectField:
        expr = data["expression"]
        if isinstance(expr, dict) and (
            ("function" in expr and "args" in expr)
            or ("expression" in expr and "params" in expr)
        ):
            expr = SqlExpression.from_dict(expr)
        return cls(expression=expr, alias=data.get("alias"))


@dataclass(frozen=True)
class SelectClause:
    fields: list[SelectField]

    def __post_init__(self):
        if not self.fields:
            raise ValueError("SelectClause must have at least one field")

    def to_sql(self) -> str:
        return "SELECT " + ", ".join(f.to_sql() for f in self.fields)

    def to_dict(self) -> dict[str, Any]:
        return {"fields": [f.to_dict() for f in self.fields]}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SelectClause:
        return cls(fields=[SelectField.from_dict(f) for f in data["fields"]])
