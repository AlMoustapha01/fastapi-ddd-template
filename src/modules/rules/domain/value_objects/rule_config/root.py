from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .join_clause import JoinClause
from .select_clause import SelectClause
from .where_clause import WhereClause, WhereCondition


# ============================================================
# FROM + RULE
# ============================================================
@dataclass(frozen=True)
class TableReference:
    name: str
    alias: str | None = None

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("Table name cannot be empty")
        if self.alias and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.alias):
            raise ValueError(f"Invalid alias: {self.alias}")

    def to_sql(self) -> str:
        return f"{self.name} {self.alias}" if self.alias else self.name

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "alias": self.alias}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TableReference:
        return cls(name=data["name"], alias=data.get("alias"))


@dataclass
class RuleConfig:
    select: SelectClause
    from_table: TableReference
    joins: list[JoinClause] = field(default_factory=list)
    where: WhereClause | None = None
    group_by: list[str] = field(default_factory=list)
    having: list[WhereCondition | WhereClause] = field(default_factory=list)
    order_by: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.select, SelectClause):
            raise ValueError("RuleConfig.select must be a SelectClause")
        if not isinstance(self.from_table, TableReference):
            raise ValueError("RuleConfig.from_table must be a TableReference")

    # ------------------------------
    # SERIALIZATION
    # ------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "select": self.select.to_dict(),
            "from_table": self.from_table.to_dict(),
            "joins": [j.to_dict() for j in self.joins],
            "where": self.where.to_dict() if self.where else None,
            "group_by": self.group_by,
            "having": [h.to_dict() for h in self.having],
            "order_by": self.order_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleConfig:
        if not data or "select" not in data or "from_table" not in data:
            raise ValueError(
                f"Invalid RuleConfig data: missing required keys. \
                    Got: {list(data.keys()) if data else 'empty'}"
            )
        where_data = data.get("where")
        return cls(
            select=SelectClause.from_dict(data["select"]),
            from_table=TableReference.from_dict(data["from_table"]),
            joins=[JoinClause.from_dict(j) for j in data.get("joins", [])],
            where=WhereClause.from_dict(where_data) if where_data else None,
            group_by=data.get("group_by", []),
            having=[WhereCondition.from_dict(h) for h in data.get("having", [])],
            order_by=data.get("order_by", []),
        )

    def validate(self) -> None:
        """Validates that the RuleConfig has valid structure"""
        if not self.select.fields:
            raise ValueError("RuleConfig must have at least one select field")
        if not self.from_table.name.strip():
            raise ValueError("RuleConfig must specify a main table")

    def get_table_names(self) -> list[str]:
        """Returns all table names used in this configuration"""
        tables = [self.from_table.name]

        # Add tables from joins
        list.extend(tables, [join.table for join in self.joins])

        return list(set(tables))  # Remove duplicates

    def to_sql(self) -> str:
        parts = [self.select.to_sql(), f"FROM {self.from_table.to_sql()}"]

        list.extend(parts, [j.to_sql() for j in self.joins])

        if self.where:
            where_sql = self.where.to_sql()
            if where_sql:
                parts.append("WHERE " + where_sql)

        if self.group_by:
            parts.append("GROUP BY " + ", ".join(self.group_by))

        if self.having:
            having_sql = " AND ".join([h.to_sql() for h in self.having])
            parts.append("HAVING " + having_sql)

        if self.order_by:
            parts.append("ORDER BY " + ", ".join(self.order_by))

        return " ".join(parts)
