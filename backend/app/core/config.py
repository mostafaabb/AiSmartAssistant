"""
Application configuration for NexusAI.
Centralized settings management using Pydantic.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Example .env file:
        APP_NAME=NexusAI
        APP_VERSION=2.0
        DEBUG=true
        DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/nexusai
        SECRET_KEY=your-secret-key-here
        OPENROUTER_API_KEY=your-api-key-here
    """

    # Application
    app_name: str = "NexusAI"
    app_version: str = "2.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nexusai"
    sql_echo: bool = False

    # Security
    secret_key: str = os.urandom(32).hex()
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite
        "http://localhost:8080",
        "http://127.0.0.1:3000",
    ]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

    # AI/LLM Configuration
    openrouter_api_key: Optional[str] = None
    default_model: str = "google/gemini-2.0-flash-exp:free"
    temperature: float = 0.7
    max_tokens: int = 4096

    # Code Execution
    code_execution_timeout: int = 60  # seconds
    max_file_size: int = 5 * 1024 * 1024  # 5MB
    max_project_files: int = 50
    allowed_extensions: list = [
        "py", "js", "html", "css", "json", "txt", "md", "ts",
        "java", "cpp", "c", "cs", "zip", "jsx", "tsx", "vue",
        "go", "rs", "rb", "php", "sql", "yaml", "yml", "xml",
        "sh", "bat", "dockerfile"
    ]

    # File storage
    workspace_dir: str = "./workspace"
    max_workspace_size: int = 10 * 1024 * 1024  # 10MB per user

    # Logging
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Session
    session_timeout_minutes: int = 1440  # 24 hours

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
