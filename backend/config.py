"""
Application configuration, loaded from environment variables.

Secrets and environment-specific values never live in source code. Copy
.env.example to .env and adjust values; .env is excluded by .gitignore.
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:  # python-dotenv is optional; values can also come from the real environment.
    from dotenv import load_dotenv

    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
except ImportError:  # pragma: no cover
    pass


def _bool(name, default):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _path(name, default):
    """Read a path setting; relative paths are resolved against the project root."""
    value = os.getenv(name, default)
    return value if os.path.isabs(value) else os.path.join(PROJECT_ROOT, value)


class Config:
    HOST = os.getenv("APP_HOST", "127.0.0.1")          # localhost only by default
    PORT = _int("APP_PORT", 5000)
    DEBUG = _bool("FLASK_DEBUG", False)                 # never enable debug in production

    DATABASE_PATH = _path("DATABASE_PATH", "instance/privacy_assessments.db")
    DATASET_PATH = _path("DATASET_PATH", "data/social_media_privacy_assessments.csv")
    FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

    RETENTION_DAYS = _int("RETENTION_DAYS", 30)          # retention limitation
    RATE_LIMIT_PER_MINUTE = _int("RATE_LIMIT_PER_MINUTE", 30)
    MAX_CONTENT_LENGTH = 16 * 1024                       # 16 KB is plenty for 53 answer codes


class TestConfig(Config):
    TESTING = True
    RATE_LIMIT_PER_MINUTE = 1000
