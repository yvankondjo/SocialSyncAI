"""Lightweight warmup helpers to mitigate Cloud Run cold starts.

This module pre-initializes external dependencies that are otherwise
lazily created on the first inbound request. By doing this during
application startup, we reduce the amount of work on the first user
message after a cold start.
"""

import asyncio
import logging
from contextlib import suppress

from app.core.redis_client import init_redis_client

logger = logging.getLogger(__name__)


async def run_startup_warmup() -> None:
    """Trigger non-blocking warmup tasks.

    The warmup currently focuses on Redis because cache misses on first
    request cause multiple Supabase round-trips. Additional tasks (like
    prefetching model metadata) can be added as needed but should remain
    short to avoid slowing the startup probe.
    """

    async def _warmup_redis():
        with suppress(Exception):
            client = await init_redis_client()
            await asyncio.wait_for(client.health_check(), timeout=2.0)
            logger.info("🔥 Redis warmup completed")

    # Fire-and-forget to avoid blocking startup
    asyncio.create_task(_warmup_redis())

