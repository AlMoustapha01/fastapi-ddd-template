"""Print the Dishka dependency graph in d2 format (https://d2lang.com)."""

import asyncio

from dishka import make_async_container
from dishka.plotter import render_d2

from app.providers import get_providers
from core.infrastructure.settings import Settings


async def main() -> None:
    container = make_async_container(*get_providers(), context={Settings: Settings()})
    try:
        print(render_d2(container))
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
