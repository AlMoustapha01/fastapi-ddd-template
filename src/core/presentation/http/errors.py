"""Render every error as RFC 9457 problem details (`application/problem+json`)."""

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Final, cast

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)

log = logging.getLogger(__name__)

PROBLEM_JSON_MEDIA_TYPE: Final[str] = "application/problem+json"

STATUS_BY_ERROR_TYPE: Final[tuple[tuple[type[DomainError], int], ...]] = (
    (NotFoundError, HTTPStatus.NOT_FOUND),
    (ConflictError, HTTPStatus.CONFLICT),
    (BusinessRuleViolationError, HTTPStatus.CONFLICT),
    (DomainValidationError, HTTPStatus.UNPROCESSABLE_CONTENT),
)


class ProblemDetails(BaseModel):
    """RFC 9457 problem details, documented in OpenAPI for error responses."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    code: str | None = None
    details: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` entries for the given error status codes."""
    return {
        code: {"model": ProblemDetails, "description": HTTPStatus(code).phrase}
        for code in status_codes
    }


def status_code_for(error: DomainError) -> int:
    for error_type, status_code in STATUS_BY_ERROR_TYPE:
        if isinstance(error, error_type):
            return status_code
    return HTTPStatus.BAD_REQUEST


def problem_response(
    *,
    status_code: int,
    detail: str | None = None,
    code: str | None = None,
    extra: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": int(status_code),
    }
    if detail is not None:
        body["detail"] = detail
    if code is not None:
        body["code"] = code
    if extra:
        body.update(extra)
    return JSONResponse(
        content=jsonable_encoder(body),
        status_code=status_code,
        headers=headers,
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(DomainError, exc)
    return problem_response(
        status_code=status_code_for(error),
        detail=error.message,
        code=error.code,
        extra={"details": error.details} if error.details else None,
    )


async def handle_request_validation_error(
    _request: Request, exc: Exception
) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    return problem_response(
        status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
        detail="The request is invalid.",
        code="request_validation_error",
        extra={"errors": error.errors()},
    )


async def handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exc)
    return problem_response(
        status_code=error.status_code, detail=str(error.detail), headers=error.headers
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    log.error(
        "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc
    )
    return problem_response(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR, code="internal_error"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
