"""API key hashing, validation, and Redis-backed caching."""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models import ApiKey
from backend.app.services.redis_client import get_redis

logger = logging.getLogger(__name__)

CACHE_PREFIX = "nex:apikey:"
CACHE_TTL_SEC = 300


def hash_api_key(plain: str) -> str:
    pepper = settings.secret_key.encode("utf-8", errors="ignore")
    return hmac.new(pepper, plain.encode("utf-8"), hashlib.sha256).hexdigest()


async def validate_api_key(db: AsyncSession, plain_key: str) -> Optional[str]:
    """
    Validate a raw API key. Returns user id as string if valid, else None.
    Updates last_used_at and optional Redis cache on success.
    """
    if not plain_key or len(plain_key) < 16:
        return None

    digest = hash_api_key(plain_key)
    r = get_redis()
    cache_key = CACHE_PREFIX + digest
    if r:
        try:
            cached = await r.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.debug("api key cache get: %s", e)

    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_hash == digest,
            ApiKey.revoked_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        return None

    now = datetime.now(timezone.utc)
    if row.expires_at is not None and row.expires_at < now:
        return None

    row.last_used_at = now
    await db.commit()

    user_id = str(row.user_id)
    if r:
        try:
            await r.setex(cache_key, CACHE_TTL_SEC, user_id)
        except Exception as e:
            logger.debug("api key cache set: %s", e)

    return user_id


async def invalidate_api_key_cache(plain_key: str) -> None:
    r = get_redis()
    if not r:
        return
    try:
        await r.delete(CACHE_PREFIX + hash_api_key(plain_key))
    except Exception:
        pass


async def invalidate_api_key_cache_by_hash(key_hash: str) -> None:
    r = get_redis()
    if not r:
        return
    try:
        await r.delete(CACHE_PREFIX + key_hash)
    except Exception:
        pass
