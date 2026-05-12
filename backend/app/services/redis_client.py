"""Optional async Redis client for caching and rate-limit storage."""

from __future__ import annotations

import logging
from typing import Optional

import redis.asyncio as redis

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    global _client
    if not settings.redis_url:
        logger.info("Redis disabled (REDIS_URL not set)")
        return
    try:
        _client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning("Redis connection failed, continuing without cache: %s", e)
        _client = None


async def close_redis() -> None:
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as e:
            logger.warning("Redis close: %s", e)
        _client = None


def get_redis() -> Optional[redis.Redis]:
    return _client
