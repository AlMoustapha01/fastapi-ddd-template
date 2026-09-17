from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class JoinType(Enum):
    INNER = "INNER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    FULL = "FULL"


# ============================================================
# JOIN
# ============================================================
@dataclass(frozen=True)
class JoinClause:
    type: JoinType
    table: str
    alias: str | None = None
    on: str | None = None
    use_as: bool = True

    def __post_init__(self):
        if not self.table.strip():
            raise ValueError("Table name cannot be empty")
        if self.alias and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.alias):
            raise ValueError(f"Invalid alias: {self.alias}")
        if not self.on or not self.on.strip():
            raise ValueError("JoinClause requires a valid ON condition")

    def to_sql(self) -> str:
        alias_sql = f" {'AS ' if self.use_as else ''}{self.alias}" if self.alias else ""
        return f"{self.type.value} JOIN {self.table}{alias_sql} ON {self.on}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "table": self.table,
            "alias": self.alias,
            "on": self.on,
            "use_as": self.use_as,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JoinClause:
        return cls(
            type=JoinType(data["type"]),
            table=data["table"],
            alias=data.get("alias"),
            on=data.get("on"),
            use_as=data.get("use_as", True),
        )
