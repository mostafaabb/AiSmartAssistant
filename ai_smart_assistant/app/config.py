"""
NexusAI Configuration Module
Manages environment variables and application settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()

    # API Keys
    OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # Application settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB upload limit
    MAX_PROJECT_FILES = 50
    CODE_EXECUTION_TIMEOUT = 60  # seconds

    # Supported file extensions
    ALLOWED_EXTENSIONS = {
        'py', 'js', 'html', 'css', 'json', 'txt', 'md', 'ts',
        'java', 'cpp', 'c', 'cs', 'zip', 'jsx', 'tsx', 'vue',
        'go', 'rs', 'rb', 'php', 'sql', 'yaml', 'yml', 'xml',
        'sh', 'bat'
    }
