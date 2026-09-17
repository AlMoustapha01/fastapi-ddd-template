"""User domain exceptions."""


class UserDomainError(Exception):
    """Base exception for user domain errors."""


class UserValidationError(UserDomainError):
    """Raised when user validation fails."""


class UserNotFoundError(UserDomainError):
    """Raised when a user is not found."""


class UserAlreadyExistsError(UserDomainError):
    """Raised when attempting to create a user that already exists."""
