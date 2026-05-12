"""Flask extensions (initialized in app factory)."""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _client_ip():
    from flask import request

    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return get_remote_address()


limiter = Limiter(key_func=_client_ip)
