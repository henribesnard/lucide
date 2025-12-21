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
    FAST_LLM_PROVIDER: Literal["deepseek", "openai"] = "openai"
    FAST_LLM_MODEL: str = "gpt-4o-mini"
    FAST_LLM_API_KEY: str = ""
    SLOW_LLM_PROVIDER: Literal["deepseek", "openai"] = "deepseek"
    SLOW_LLM_MODEL: str = "deepseek-chat"
    SLOW_LLM_API_KEY: str = ""

    # Football API
    FOOTBALL_API_KEY: str = ""
    FOOTBALL_API_BASE_URL: str = "https://v3.football.api-sports.io"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    ENABLE_REDIS_CACHE: bool = True

    # App
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_PARALLEL_API_CALLS: bool = True
    MAX_PARALLEL_TOOL_CALLS: int = 5
    ENABLE_FAST_LLM: bool = False
    ENABLE_SMART_SKIP_ANALYSIS: bool = False


settings = Settings()
