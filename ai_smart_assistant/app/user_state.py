"""
Per-browser application state (chat history, code context, execution errors).

Uses a signed Flask session cookie to identify the browser, and an in-process
store for data. Safe under threaded Werkzeug/Gunicorn when accessed only
through the helpers in this module.

For multiple Gunicorn workers, use --workers 1 (or sticky sessions and accept
split state); each worker has its own memory.
"""

from __future__ import annotations

import copy
import time
import uuid
from threading import RLock

from flask import session

_lock = RLock()
_states: dict[str, dict] = {}
_last_seen: dict[str, float] = {}

SESSION_KEY = "nexus_sid"


def _max_sessions() -> int:
    try:
        from flask import current_app

        return int(current_app.config.get("MAX_SERVER_SESSIONS", 2000))
    except RuntimeError:
        return 2000


def _touch(sid: str) -> None:
    _last_seen[sid] = time.time()


def _ensure_sid() -> str:
    if SESSION_KEY not in session:
        session[SESSION_KEY] = str(uuid.uuid4())
        session.permanent = True
        session.modified = True
    return session[SESSION_KEY]


def _evict() -> None:
    max_n = _max_sessions()
    if len(_states) <= max_n:
        return
    overflow = len(_states) - max_n
    for sid, _ in sorted(_last_seen.items(), key=lambda x: x[1])[:overflow]:
        _states.pop(sid, None)
        _last_seen.pop(sid, None)


def _ensure_bucket(sid: str) -> dict:
    _touch(sid)
    if sid not in _states:
        _evict()
        _states[sid] = {
            "history": [],
            "code_context": None,
            "last_execution_error": None,
        }
    return _states[sid]


def template_payload() -> dict:
    """Data for rendering the main page (copies safe for templates)."""
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        return {
            "history": list(st["history"]),
            "code_context": copy.deepcopy(st["code_context"]),
        }


def snapshot_for_chat() -> tuple:
    """Consistent read for building the AI prompt: context, last_error."""
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        return copy.deepcopy(st.get("code_context")), st.get("last_execution_error")


def append_history_user(content: str) -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["history"].append({"role": "user", "content": content})


def append_history_assistant(content: str) -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["history"].append({"role": "assistant", "content": content})


def clear_last_execution_error() -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["last_execution_error"] = None


def set_last_execution_error(message: str | None) -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["last_execution_error"] = message


def set_code_context(ctx: dict | None) -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["code_context"] = ctx


def get_code_context():
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        return st.get("code_context")


def clear_code_context() -> None:
    set_code_context(None)


def clear_all() -> None:
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        st["history"] = []
        st["code_context"] = None
        st["last_execution_error"] = None


def get_history_copy():
    sid = _ensure_sid()
    with _lock:
        st = _ensure_bucket(sid)
        return list(st["history"])


def health_metrics_for_session() -> tuple[int, bool]:
    """History length and whether code context is set (dev health only)."""
    sid = _ensure_sid()
    with _lock:
        if sid not in _states:
            return 0, False
        st = _states[sid]
        return len(st["history"]), st["code_context"] is not None
