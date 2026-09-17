"""Liveness and readiness probes."""

import logging
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

log = logging.getLogger(__name__)


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["Health"])

    @router.get("/health", summary="Liveness probe")
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @router.get(
        "/health/ready",
        summary="Readiness probe (checks the database)",
        responses={HTTPStatus.SERVICE_UNAVAILABLE: {"description": "Database down"}},
    )
    @inject
    async def readiness(engine: FromDishka[AsyncEngine]) -> JSONResponse:
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            log.warning("Readiness check failed: database unavailable", exc_info=True)
            return JSONResponse(
                {"status": "unavailable"}, status_code=HTTPStatus.SERVICE_UNAVAILABLE
            )
        return JSONResponse({"status": "ok"})

    return router
