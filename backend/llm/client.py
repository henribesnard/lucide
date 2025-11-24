from openai import AsyncOpenAI
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Lightweight wrapper around OpenAI-compatible chat endpoints (DeepSeek by default).
    Keeps the signature uniform for chat completions with optional tool calling and JSON mode.
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = provider

        if provider == "deepseek":
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY is required")
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url or "https://api.deepseek.com",
            )
            self.model = model or "deepseek-chat"
            logger.info("LLM client initialised with DeepSeek")

        elif provider == "openai":
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required")
            self.client = AsyncOpenAI(api_key=api_key)
            self.model = model or "gpt-4-turbo-preview"
            logger.info("LLM client initialised with OpenAI")

        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ):
        """
        Uniform chat completion call with optional tools and JSON response format.
        """
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        if response_format:
            kwargs["response_format"] = response_format

        try:
            return await self.client.chat.completions.create(**kwargs)
        except Exception as exc:
            logger.error(f"LLM API error: {exc}")
            raise

    def get_provider_info(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "model": self.model,
        }
