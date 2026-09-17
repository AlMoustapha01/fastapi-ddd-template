from enum import StrEnum


class RuleStatus(StrEnum):
    DRAFT = "DRAFT"
    IN_PRODUCTION = "IN_PRODUCTION"
    TO_VALIDATE = "TO_VALIDATE"
    ARCHIVED = "ARCHIVED"
