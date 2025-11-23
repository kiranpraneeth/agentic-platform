"""Application configuration."""

from typing import Any

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # API
    PROJECT_NAME: str = "Agentic Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"
    ALLOWED_ORIGINS: str = "*"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: RedisDsn
    REDIS_POOL_SIZE: int = 10

    # LLM Providers
    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # Agent Execution
    DEFAULT_AGENT_TIMEOUT: int = 300  # 5 minutes
    MAX_AGENT_ITERATIONS: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"  # development, staging, production

    # Error Tracking
    SENTRY_DSN: str | None = None

    @field_validator("ALLOWED_ORIGINS", mode="after")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> list[str]:
        """Parse allowed origins from string."""
        if v:
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return ["*"]


settings = Settings()
