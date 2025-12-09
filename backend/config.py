from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from dotenv import load_dotenv

# Force reload .env to ensure fresh values
load_dotenv(override=True)


class Settings(BaseSettings):
    """Configuration de l'application LUCIDE."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",
    )

    # LLM configuration
    LLM_PROVIDER: Literal["deepseek", "openai"] = "deepseek"
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Football API
    FOOTBALL_API_KEY: str = ""
    FOOTBALL_API_BASE_URL: str = "https://v3.football.api-sports.io"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # App
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"


settings = Settings()
