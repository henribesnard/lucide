"""
Telegram Bot Configuration

Handles configuration for the Telegram bot including environment variables.
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class TelegramBotSettings(BaseSettings):
    """Telegram bot settings loaded from environment variables."""

    # Telegram Bot Token (from @BotFather)
    TELEGRAM_BOT_TOKEN: str = ""  # Default empty for testing

    # Webhook configuration
    TELEGRAM_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_WEBHOOK_PATH: str = "/telegram/webhook"
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None

    # Bot configuration
    TELEGRAM_BOT_USERNAME: Optional[str] = None
    TELEGRAM_MAX_MESSAGE_LENGTH: int = 4096
    TELEGRAM_TYPING_ACTION_TIMEOUT: int = 5  # seconds

    # Rate limiting
    TELEGRAM_RATE_LIMIT_MESSAGES: int = 30  # messages per minute
    TELEGRAM_RATE_LIMIT_WINDOW: int = 60  # seconds

    # Feature flags
    TELEGRAM_ENABLE_GROUPS: bool = True
    TELEGRAM_ENABLE_INLINE_MODE: bool = True
    TELEGRAM_ENABLE_PAYMENTS: bool = False

    # Backend integration
    BACKEND_BASE_URL: str = "http://localhost:8000"

    # Redis for rate limiting and sessions
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_DB: int = 1  # Use different DB than main backend

    # PostgreSQL database (same as main backend)
    DATABASE_URL: str = "postgresql://localhost/lucide_test"  # Default for testing

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        # Look for .env in the same directory as this config file
        env_file = str(Path(__file__).parent / ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields


# Global settings instance
try:
    telegram_settings = TelegramBotSettings()
except Exception as e:
    # For testing, create with defaults
    import warnings
    warnings.warn(f"Failed to load settings from .env: {e}. Using defaults.")
    telegram_settings = TelegramBotSettings(
        TELEGRAM_BOT_TOKEN="test_token",
        DATABASE_URL="postgresql://localhost/lucide_test",
    )
