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
    # Multi-LLM support: Slow (DeepSeek), Medium (GPT-4o-mini), Fast (GPT-4o)
    SLOW_LLM_PROVIDER: Literal["deepseek", "openai"] = "deepseek"
    SLOW_LLM_MODEL: str = "deepseek-chat"
    SLOW_LLM_API_KEY: str = ""
    MEDIUM_LLM_PROVIDER: Literal["deepseek", "openai"] = "openai"
    MEDIUM_LLM_MODEL: str = "gpt-4o-mini"
    MEDIUM_LLM_API_KEY: str = ""
    FAST_LLM_PROVIDER: Literal["deepseek", "openai"] = "openai"
    FAST_LLM_MODEL: str = "gpt-4o"
    FAST_LLM_API_KEY: str = ""

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
    ENABLE_MULTI_LLM: bool = False
    ENABLE_SMART_SKIP_ANALYSIS: bool = False

    # CORS - comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost,http://localhost:3000,http://localhost:3001,http://localhost:3010,http://localhost:8000,http://localhost:8001"


settings = Settings()
