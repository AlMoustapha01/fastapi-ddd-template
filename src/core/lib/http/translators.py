from fastapi_error_map import ErrorTranslator, SimpleErrorResponseModel
from pydantic import BaseModel

from core.lib.base.domain_error import DomainError


class ServiceUnavailableTranslator(ErrorTranslator[SimpleErrorResponseModel]):
    @property
    def error_response_model_cls(self) -> type[SimpleErrorResponseModel]:
        return SimpleErrorResponseModel

    def from_error(self, err: Exception) -> SimpleErrorResponseModel:  # noqa: ARG002
        return SimpleErrorResponseModel(
            error="Service temporarily unavailable. Please try again later."
        )


class DomainErrorResponseModel(BaseModel):
    """Response model for domain errors with code."""

    error: str
    code: str | None = None


class DomainErrorTranslator(ErrorTranslator[DomainErrorResponseModel]):
    """Global translator for DomainError exceptions."""

    @property
    def error_response_model_cls(self) -> type[DomainErrorResponseModel]:
        return DomainErrorResponseModel

    def from_error(self, err: Exception) -> DomainErrorResponseModel:
        """
        Translate DomainError to structured error response.

        Returns:
            DomainErrorResponseModel with 'error' (message) and 'code' fields
        """
        if isinstance(err, DomainError):
            return DomainErrorResponseModel(
                error=err.message,
                code=err.code,
            )

        # Fallback for non-DomainError exceptions
        return DomainErrorResponseModel(
            error=str(err),
            code="INTERNAL_ERROR",
        )
