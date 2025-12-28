"""
DataPulse Configuration

Centralized configuration management using Pydantic BaseSettings.
All configuration values are loaded from environment variables with sensible defaults.

Usage:
    from backend.config import settings
    print(settings.MAX_ROWS)

Environment Variables:
    See .env.example for all available options.

Copyright (c) 2024 Luca Neviani
Licensed under the MIT License
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # ==========================================================================
    # Application
    # ==========================================================================
    APP_NAME: str = Field(default="DataPulse", description="Application name")
    APP_VERSION: str = Field(default="2.1.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")

    # ==========================================================================
    # API Configuration
    # ==========================================================================
    API_HOST: str = Field(default="127.0.0.1", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_WORKERS: int = Field(default=1, description="Number of API workers")
    API_PREFIX: str = Field(default="/api", description="API prefix")

    # ==========================================================================
    # Security
    # ==========================================================================
    CORS_ORIGINS: str = Field(default="", description="Comma-separated list of allowed origins. Empty = localhost only")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration in hours")
    SECRET_KEY_FILE: str = Field(default="data/.jwt_secret", description="Path to JWT secret file")

    # ==========================================================================
    # Database
    # ==========================================================================
    DATABASE_URL: str = Field(default="sqlite:///data/database.db", description="Database connection URL")
    DATABASE_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time in seconds")

    # ==========================================================================
    # AI Service
    # ==========================================================================
    GOOGLE_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    AI_MODEL: str = Field(default="gemini-2.0-flash-exp", description="AI model to use")
    AI_TEMPERATURE: float = Field(default=0.1, description="AI temperature (0-1)")
    AI_MAX_TOKENS: int = Field(default=500, description="Max tokens in AI response")

    # ==========================================================================
    # Rate Limiting
    # ==========================================================================
    RATE_LIMIT_REQUESTS: int = Field(default=30, description="Max requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # ==========================================================================
    # Cache
    # ==========================================================================
    CACHE_MAX_SIZE: int = Field(default=100, description="Max cache entries")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")

    # ==========================================================================
    # Query Limits
    # ==========================================================================
    MAX_ROWS: int = Field(default=1000, description="Max rows returned per query")
    MAX_QUERY_LENGTH: int = Field(default=500, description="Max query length")
    QUERY_TIMEOUT: int = Field(default=30, description="Query timeout in seconds")

    # ==========================================================================
    # Session Management
    # ==========================================================================
    SESSION_TTL_HOURS: int = Field(default=4, description="Session TTL in hours")
    MAX_SESSIONS_PER_USER: int = Field(default=5, description="Max sessions per user")

    # ==========================================================================
    # File Upload
    # ==========================================================================
    MAX_UPLOAD_SIZE_MB: int = Field(default=50, description="Max upload size in MB")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=["csv", "xlsx", "xls", "db", "sqlite", "sqlite3"], description="Allowed file extensions for upload"
    )
    UPLOAD_DIR: str = Field(default="uploads", description="Upload directory")

    # ==========================================================================
    # Export
    # ==========================================================================
    EXPORT_DIR: str = Field(default="exports", description="Export directory")
    MAX_EXPORT_ROWS: int = Field(default=10000, description="Max rows for export")

    # ==========================================================================
    # Logging
    # ==========================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path (optional)")

    # ==========================================================================
    # Frontend
    # ==========================================================================
    FRONTEND_URL: str = Field(default="http://localhost:8501", description="Frontend URL")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.CORS_ORIGINS:
            return ["http://localhost:8501", "http://127.0.0.1:8501", "http://localhost:3000"]
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def max_upload_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


# ==========================================================================
# Validation
# ==========================================================================


def validate_settings() -> List[str]:
    """Validate settings and return list of warnings."""
    warnings = []

    if not settings.GOOGLE_API_KEY:
        warnings.append("GOOGLE_API_KEY not set - AI features will be disabled")

    if settings.is_production:
        if not settings.CORS_ORIGINS:
            warnings.append("CORS_ORIGINS not set in production - using localhost defaults")
        if settings.DEBUG:
            warnings.append("DEBUG mode enabled in production - disable for security")
        if settings.CORS_ORIGINS == "*":
            warnings.append("CORS_ORIGINS='*' is insecure in production")

    return warnings


# ==========================================================================
# Export for easy access
# ==========================================================================

__all__ = ["settings", "get_settings", "Settings", "validate_settings"]
