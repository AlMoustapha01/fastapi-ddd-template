from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any


# ---------------------------------
# Aggregations (standard SQL)
# ---------------------------------
class NumericAggregation(StrEnum):
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT(DISTINCT {})"
    STDDEV = "STDDEV"
    STDDEV_POP = "STDDEV_POP"
    STDDEV_SAMP = "STDDEV_SAMP"
    VARIANCE = "VARIANCE"
    VAR_POP = "VAR_POP"
    VAR_SAMP = "VAR_SAMP"
    MEDIAN = "MEDIAN"
    MODE = "MODE"
    PERCENTILE_CONT = "PERCENTILE_CONT"
    PERCENTILE_DISC = "PERCENTILE_DISC"


# ---------------------------------
# Numeric functions
# ---------------------------------
class NumericFunction(StrEnum):
    # Basic math
    ABS = "ABS"
    ROUND = "ROUND"
    CEIL = "CEIL"
    CEILING = "CEILING"
    FLOOR = "FLOOR"
    TRUNC = "TRUNC"
    TRUNCATE = "TRUNCATE"
    SIGN = "SIGN"

    # Power and roots
    POWER = "POWER"
    POW = "POW"
    SQRT = "SQRT"
    SQUARE = "SQUARE"

    # Exponential and logarithmic
    EXP = "EXP"
    LN = "LN"
    LOG = "LOG"
    LOG10 = "LOG10"
    LOG2 = "LOG2"

    # Modulo and division
    MOD = "MOD"
    REMAINDER = "REMAINDER"

    # Trigonometric
    SIN = "SIN"
    COS = "COS"
    TAN = "TAN"
    ASIN = "ASIN"
    ACOS = "ACOS"
    ATAN = "ATAN"
    ATAN2 = "ATAN2"

    # Hyperbolic
    SINH = "SINH"
    COSH = "COSH"
    TANH = "TANH"

    # Random
    RANDOM = "RANDOM"
    RAND = "RAND"

    # Constants
    PI = "PI"
    E = "E"


# ---------------------------------
# String functions
# ---------------------------------
class StringFunction(StrEnum):
    # Length and size
    LENGTH = "LENGTH"
    LEN = "LEN"
    CHAR_LENGTH = "CHAR_LENGTH"
    CHARACTER_LENGTH = "CHARACTER_LENGTH"

    # Case conversion
    UPPER = "UPPER"
    LOWER = "LOWER"
    INITCAP = "INITCAP"

    # Trimming and padding
    TRIM = "TRIM"
    LTRIM = "LTRIM"
    RTRIM = "RTRIM"
    LPAD = "LPAD"
    RPAD = "RPAD"

    # Substring operations
    SUBSTRING = "SUBSTRING"
    SUBSTR = "SUBSTR"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    MID = "MID"

    # Search and replace
    REPLACE = "REPLACE"
    TRANSLATE = "TRANSLATE"
    REVERSE = "REVERSE"

    # Position and search
    POSITION = "POSITION"
    LOCATE = "LOCATE"
    INSTR = "INSTR"
    CHARINDEX = "CHARINDEX"

    # Concatenation
    CONCAT = "CONCAT"
    CONCAT_WS = "CONCAT_WS"

    # Encoding
    ASCII = "ASCII"
    CHR = "CHR"
    CHAR = "CHAR"

    # Pattern matching
    LIKE = "LIKE"
    REGEXP = "REGEXP"
    REGEXP_REPLACE = "REGEXP_REPLACE"
    REGEXP_SUBSTR = "REGEXP_SUBSTR"


# ---------------------------------
# Date/Time functions
# ---------------------------------
class DateTimeFunction(StrEnum):
    # Current date/time
    NOW = "NOW"
    CURRENT_DATE = "CURRENT_DATE"
    CURRENT_TIME = "CURRENT_TIME"
    CURRENT_TIMESTAMP = "CURRENT_TIMESTAMP"
    GETDATE = "GETDATE"
    SYSDATE = "SYSDATE"

    # Date parts extraction
    YEAR = "YEAR"
    MONTH = "MONTH"
    DAY = "DAY"
    HOUR = "HOUR"
    MINUTE = "MINUTE"
    SECOND = "SECOND"
    DAYOFWEEK = "DAYOFWEEK"
    DAYOFYEAR = "DAYOFYEAR"
    WEEK = "WEEK"
    QUARTER = "QUARTER"

    # Date arithmetic
    DATEADD = "DATEADD"
    DATEDIFF = "DATEDIFF"
    DATE_ADD = "DATE_ADD"
    DATE_SUB = "DATE_SUB"
    ADDDATE = "ADDDATE"
    SUBDATE = "SUBDATE"

    # Date formatting
    DATE_FORMAT = "DATE_FORMAT"
    FORMAT = "FORMAT"
    TO_CHAR = "TO_CHAR"
    TO_DATE = "TO_DATE"

    # Date conversion
    CAST = "CAST"
    CONVERT = "CONVERT"
    STR_TO_DATE = "STR_TO_DATE"

    # Date validation
    ISDATE = "ISDATE"

    # Timezone
    UTC_TIMESTAMP = "UTC_TIMESTAMP"
    CONVERT_TZ = "CONVERT_TZ"


# ---------------------------------
# Conditional functions
# ---------------------------------
class ConditionalFunction(StrEnum):
    CASE = "CASE"
    IF = "IF"
    IIF = "IIF"
    NULLIF = "NULLIF"
    ISNULL = "ISNULL"
    IFNULL = "IFNULL"
    NVL = "NVL"
    NVL2 = "NVL2"
    COALESCE = "COALESCE"
    GREATEST = "GREATEST"
    LEAST = "LEAST"


# ---------------------------------
# Type conversion functions
# ---------------------------------
class ConversionFunction(StrEnum):
    CAST = "CAST"
    CONVERT = "CONVERT"
    TO_NUMBER = "TO_NUMBER"
    TO_CHAR = "TO_CHAR"
    TO_DATE = "TO_DATE"
    STR = "STR"
    VAL = "VAL"
    INT = "INT"
    FLOAT = "FLOAT"
    DECIMAL = "DECIMAL"


# -------------------------------
# SQL Expressions (functions etc.)
# -------------------------------
# ============================================================
# SQL Expressions
# ============================================================
@dataclass(frozen=True)
class SqlExpression:
    function: str
    args: list[str | SqlExpression | int | float | bool | datetime | date]

    def __post_init__(self):
        if not self.function:
            raise ValueError("Function name cannot be empty")
        if not self.args:
            raise ValueError("SqlExpression must have at least one argument")

    def to_sql(self) -> str:
        func_name = self.function
        parts = []
        for arg in self.args:
            if isinstance(arg, SqlExpression):
                parts.append(arg.to_sql())
            elif isinstance(arg, str):
                if re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", arg):  # colonne
                    parts.append(arg)
                else:  # littéral string
                    safe = arg.replace("'", "''")
                    parts.append(f"'{safe}'")
            elif isinstance(arg, bool):
                parts.append("TRUE" if arg else "FALSE")
            elif isinstance(arg, (int, float)):
                parts.append(str(arg))
            elif isinstance(arg, datetime):
                parts.append(f"'{arg.strftime('%Y-%m-%d %H:%M:%S')}'")
            elif isinstance(arg, date):
                parts.append(f"'{arg.strftime('%Y-%m-%d')}'")
            else:
                raise ValueError(f"Unsupported argument type: {type(arg)}")
        return f"{func_name.upper()}({', '.join(parts)})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "function": self.function,
            "args": [
                a.to_dict() if isinstance(a, SqlExpression) else a for a in self.args
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SqlExpression:
        if "function" in data and "args" in data:
            args = [
                SqlExpression.from_dict(a)
                if isinstance(a, dict) and "function" in a
                else a
                for a in data["args"]
            ]
            return cls(function=data["function"], args=args)

        if "expression" in data and "params" in data:
            params = data["params"]
            args_list: list[Any] = []
            if "args" in params:
                args_list = params["args"]
            else:
                i = 0
                while f"arg{i}" in params:
                    args_list.append(params[f"arg{i}"])
                    i += 1
            args = [
                SqlExpression.from_dict(a)
                if isinstance(a, dict) and ("function" in a or "expression" in a)
                else a
                for a in args_list
            ]
            return cls(function=data["expression"], args=args)

        raise ValueError(f"Invalid SqlExpression data: unrecognized format in {data}")
