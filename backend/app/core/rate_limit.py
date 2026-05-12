"""Shared SlowAPI limiter (Redis-backed when REDIS_URL is set)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.core.config import settings


def _storage_uri() -> str:
    if settings.redis_url:
        return settings.redis_url
    return "memory://"


limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri())
