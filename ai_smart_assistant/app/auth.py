"""
NexusAI Authentication Module
Lightweight user authentication using SQLite + Werkzeug password hashing.
No external ORM dependency — uses Python's built-in sqlite3 module.
"""

import os
import re
import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager

from werkzeug.security import generate_password_hash, check_password_hash

# Database path — sits next to the project root
_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
DB_PATH = os.path.join(_DB_DIR, "nexusai_users.db")

# Username & email validation
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _init_db():
    """Create the users table if it doesn't already exist."""
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                username    TEXT UNIQUE NOT NULL,
                email       TEXT UNIQUE NOT NULL,
                password    TEXT NOT NULL,
                full_name   TEXT DEFAULT '',
                created_at  TEXT NOT NULL,
                last_login  TEXT
            )
        """)


@contextmanager
def _get_db():
    """Yield a sqlite3 connection that auto-commits on success."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def register_user(username: str, email: str, password: str, full_name: str = "") -> dict:
    """Register a new user.

    Returns:
        dict with 'success' bool and 'error' message on failure.
    """
    username = username.strip()
    email = email.strip().lower()
    full_name = full_name.strip()

    # Validation
    if not USERNAME_RE.match(username):
        return {"success": False, "error": "Username must be 3-30 characters (letters, numbers, underscores only)."}

    if not EMAIL_RE.match(email):
        return {"success": False, "error": "Please enter a valid email address."}

    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters."}

    hashed = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)
    user_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    try:
        with _get_db() as conn:
            conn.execute(
                "INSERT INTO users (id, username, email, password, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, email, hashed, full_name, now),
            )
        return {"success": True, "user_id": user_id}
    except sqlite3.IntegrityError as e:
        err = str(e).lower()
        if "username" in err:
            return {"success": False, "error": "That username is already taken."}
        if "email" in err:
            return {"success": False, "error": "An account with that email already exists."}
        return {"success": False, "error": "Registration failed. Please try again."}


def authenticate_user(login: str, password: str) -> dict:
    """Authenticate by username or email.

    Returns:
        dict with 'success' bool, 'user' dict on success, 'error' on failure.
    """
    login = login.strip()
    if not login or not password:
        return {"success": False, "error": "Please enter your credentials."}

    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (login, login.lower()),
        ).fetchone()

    if not row:
        return {"success": False, "error": "Invalid username/email or password."}

    if not check_password_hash(row["password"], password):
        return {"success": False, "error": "Invalid username/email or password."}

    # Update last login
    now = datetime.utcnow().isoformat()
    with _get_db() as conn:
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))

    return {
        "success": True,
        "user": {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "full_name": row["full_name"],
        },
    }


def get_user_by_id(user_id: str) -> dict | None:
    """Fetch a user by ID (for session lookup)."""
    with _get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "full_name": row["full_name"],
    }


# Auto-init on import
_init_db()
