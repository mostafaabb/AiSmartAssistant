"""Git remote URL validation for clone endpoints."""

from __future__ import annotations

from urllib.parse import urlparse


def is_allowed_git_remote(url: str, allowed_hosts: frozenset[str]) -> bool:
    if not url or not isinstance(url, str):
        return False
    u = urlparse(url.strip())
    if u.scheme not in ("http", "https"):
        return False
    host = (u.hostname or "").lower()
    if not host:
        return False
    return host in allowed_hosts
