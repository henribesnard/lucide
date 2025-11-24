import json
import logging
from typing import Any, Dict

from backend.llm.client import LLMClient
from backend.prompts import INTENT_SYSTEM_PROMPT
from backend.agents.types import IntentResult

logger = logging.getLogger(__name__)


class IntentAgent:
    """Detects user intent and extracts entities before any tool call."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(self, user_message: str) -> IntentResult:
        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        try:
            try:
                response = await self.llm.chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=400,
                    response_format={"type": "json_object"},
                )
            except Exception as exc:
                logger.warning(f"Intent agent json mode failed, retrying without format: {exc}")
                response = await self.llm.chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=400,
                )
            raw_content = response.choices[0].message.content or "{}"
            payload: Dict[str, Any] = json.loads(raw_content)
            intent = str(payload.get("intent") or "info_generale")
            needs_data = bool(payload.get("needs_data", True))
            entities = payload.get("entities") or {}
            confidence = float(payload.get("confidence", 0.0))
            reasoning = str(payload.get("reasoning") or "").strip()
            return IntentResult(
                intent=intent,
                entities=entities,
                needs_data=needs_data,
                confidence=confidence,
                reasoning=reasoning,
            )
        except Exception as exc:
            logger.error(f"Intent agent failed: {exc}", exc_info=True)
            return IntentResult(
                intent="info_generale",
                entities={"fallback": True},
                needs_data=False,
                confidence=0.0,
                reasoning="Fallback intent because parsing failed",
            )
