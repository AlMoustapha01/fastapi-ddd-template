"""Application lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Close the Dishka container, which disposes the database engine, on shutdown."""
    yield
    await app.state.dishka_container.close()
