"""Application configuration for different environments."""

import os
from typing import Type


class Config:
    """Base configuration class."""

    # Flask settings
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False

    # CORS settings
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Upload and processing directories
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", os.path.join(os.getcwd(), "uploads"))
    TEMP_DIR = os.getenv("TEMP_DIR", os.path.join(os.getcwd(), "temp"))
    SCANS_DIR = os.getenv("SCANS_DIR", os.path.join(os.getcwd(), "scans"))

    # File upload limits
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

    # Image processing config
    BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", 100.0))
    THUMBNAIL_SIZE = tuple(map(int, os.getenv("THUMBNAIL_SIZE", "200,200").split(",")))

    # Logging
    LOG_LEVEL = "INFO"


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    LOG_LEVEL = "DEBUG"


class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    # Use in-memory database for testing
    UPLOAD_DIR = "/tmp/test_uploads"
    TEMP_DIR = "/tmp/test_temp"
    SCANS_DIR = "/tmp/test_scans"


class ProductionConfig(Config):
    """Production environment configuration."""

    # Production settings
    LOG_LEVEL = "WARNING"


def get_config() -> Type[Config]:
    """Get configuration class based on environment.

    Returns:
        Type[Config]: Configuration class for the current environment.
    """
    env = os.getenv("FLASK_ENV", "development").lower()

    if env == "testing":
        return TestingConfig
    elif env == "production":
        return ProductionConfig
    else:
        return DevelopmentConfig
