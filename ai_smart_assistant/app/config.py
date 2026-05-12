"""
NexusAI Configuration Module
Manages environment variables and application settings.
"""

import os
import sys
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _is_production_env() -> bool:
    return os.environ.get("FLASK_ENV", "").lower() == "production" or _bool(
        "NEXUS_PRODUCTION", False
    )


class Config:
    """Base application configuration."""

    # Environment
    ENV = "development"
    DEBUG = True
    TESTING = False

    # Security — must be set in production (validated in ProductionConfig)
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

    # Public URL (used for OpenRouter Referer header and redirects behind HTTPS)
    APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5000").rstrip("/")

    # API Keys
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

    # Session (Flask signed cookie identifies browser; see user_state.py)
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.environ.get("SESSION_LIFETIME_HOURS", "168"))
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", False)

    # Reverse proxy (nginx, Traefik, Cloudflare)
    TRUST_PROXY = _bool("TRUST_PROXY", False)
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "http")

    # Limits
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024)))
    MAX_PROJECT_FILES = int(os.environ.get("MAX_PROJECT_FILES", "50"))
    MAX_SERVER_SESSIONS = int(os.environ.get("MAX_SERVER_SESSIONS", "2000"))
    CODE_EXECUTION_TIMEOUT = int(os.environ.get("CODE_EXECUTION_TIMEOUT", "60"))

    # Rate limiting (Flask-Limiter)
    RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", True)
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    # git clone — host allowlist (comma-separated)
    _git_hosts = os.environ.get(
        "GIT_ALLOWED_HOSTS",
        "github.com,www.github.com,gitlab.com,www.gitlab.com,bitbucket.org",
    )
    GIT_ALLOWED_HOSTS = frozenset(
        h.strip().lower() for h in _git_hosts.split(",") if h.strip()
    )

    # Supported file extensions
    ALLOWED_EXTENSIONS = {
        "py",
        "js",
        "html",
        "css",
        "json",
        "txt",
        "md",
        "ts",
        "java",
        "cpp",
        "c",
        "cs",
        "zip",
        "jsx",
        "tsx",
        "vue",
        "go",
        "rs",
        "rb",
        "php",
        "sql",
        "yaml",
        "yml",
        "xml",
        "sh",
        "bat",
    }


class ProductionConfig(Config):
    """Production defaults — debug off, stricter cookies when behind HTTPS."""

    ENV = "production"
    DEBUG = False
    TESTING = False

    SESSION_COOKIE_SECURE = _bool("SESSION_COOKIE_SECURE", True)
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")


def enforce_production_secrets() -> None:
    """Exit the process if production secrets are missing or weak."""
    if not _is_production_env():
        return
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        print(
            "FATAL: SECRET_KEY must be set in production. "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"',
            file=sys.stderr,
        )
        sys.exit(1)
    weak = {
        "your-super-secret-key-change-in-production",
        "change-me",
        "secret",
    }
    if secret in weak or len(secret) < 32:
        print(
            "FATAL: SECRET_KEY must be a strong, unique value in production (min 32 characters).",
            file=sys.stderr,
        )
        sys.exit(1)


class DevelopmentConfig(Config):
    """Local development."""

    ENV = "development"
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = _bool("RATELIMIT_ENABLED", False)


def select_config():
    """Choose config class from environment."""
    if _is_production_env():
        return ProductionConfig
    return DevelopmentConfig
