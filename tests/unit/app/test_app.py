"""Application factory, error rendering and health probes (no database needed)."""

from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.main import create_app
from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)
from core.infrastructure.settings import (
    AppSettings,
    CorsSettings,
    DatabaseSettings,
    Settings,
)

UNREACHABLE_DATABASE = DatabaseSettings(
    host="127.0.0.1", port=1, password=SecretStr("unused")
)


def make_settings(
    *, docs_enabled: bool = True, allow_origins: list[str] | None = None
) -> Settings:
    return Settings(
        app=AppSettings(docs_enabled=docs_enabled),
        database=UNREACHABLE_DATABASE,
        cors=CorsSettings(allow_origins=allow_origins or []),
        _env_file=None,
    )


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    application = create_app(make_settings())
    yield application
    await application.state.dishka_container.close()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


async def test_readiness_reports_an_unreachable_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"status": "unavailable"}


async def test_root_redirects_to_docs(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert response.headers["location"] == "/docs"


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (NotFoundError("Missing.", code="thing_not_found"), HTTPStatus.NOT_FOUND),
        (ConflictError("Taken."), HTTPStatus.CONFLICT),
        (BusinessRuleViolationError("Not allowed."), HTTPStatus.CONFLICT),
        (DomainValidationError("Invalid."), HTTPStatus.UNPROCESSABLE_CONTENT),
        (DomainError("Bad request."), HTTPStatus.BAD_REQUEST),
    ],
)
async def test_domain_errors_are_problem_details(
    app: FastAPI, client: AsyncClient, error: DomainError, status_code: HTTPStatus
) -> None:
    async def raise_error() -> None:
        raise error

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.status_code == status_code
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": status_code.phrase,
        "status": status_code,
        "detail": error.message,
        "code": error.code,
    }


async def test_domain_error_details_are_included(
    app: FastAPI, client: AsyncClient
) -> None:
    async def raise_error() -> None:
        raise NotFoundError("Missing.", details={"id": "42"})

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.json()["details"] == {"id": "42"}


async def test_unexpected_errors_return_a_generic_500(
    app: FastAPI, client: AsyncClient
) -> None:
    async def raise_error() -> None:
        raise RuntimeError("secret internals")

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "code": "internal_error",
    }
    assert "secret internals" not in response.text


async def test_request_validation_errors_are_problem_details(
    app: FastAPI, client: AsyncClient
) -> None:
    async def read_items(limit: int) -> dict[str, int]:
        return {"limit": limit}

    app.add_api_route("/items", read_items)

    response = await client.get("/items", params={"limit": "abc"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "request_validation_error"
    assert body["errors"][0]["loc"] == ["query", "limit"]


async def test_unknown_routes_are_problem_details(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "Not Found"


async def test_docs_can_be_disabled() -> None:
    application = create_app(make_settings(docs_enabled=False))
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for path in ("/", "/docs", "/redoc", "/openapi.json"):
                response = await client.get(path)
                assert response.status_code == HTTPStatus.NOT_FOUND, path
    finally:
        await application.state.dishka_container.close()


async def test_cors_is_enabled_for_configured_origins() -> None:
    origin = "http://localhost:3000"
    application = create_app(make_settings(allow_origins=[origin]))
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
    finally:
        await application.state.dishka_container.close()
