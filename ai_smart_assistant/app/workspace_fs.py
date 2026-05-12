"""Safe path operations under the server `workspace/` directory."""

from __future__ import annotations

import os

WORKSPACE_DIR = "workspace"


def workspace_root() -> str:
    return os.path.abspath(os.path.join(os.getcwd(), WORKSPACE_DIR))


def ensure_workspace() -> str:
    root = workspace_root()
    os.makedirs(root, exist_ok=True)
    return root


def safe_join(relative_path: str) -> str | None:
    """Return absolute path inside workspace, or None if path escapes."""
    root = workspace_root()
    # Normalize: strip leading slashes and drive noise
    rel = relative_path.replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        return None
    abs_path = os.path.abspath(os.path.join(root, *rel.split("/")))
    if not abs_path.startswith(root + os.sep) and abs_path != root:
        return None
    return abs_path
