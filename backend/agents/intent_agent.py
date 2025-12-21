import json
import logging
from typing import Any, Dict, Optional

from backend.llm.client import LLMClient
from backend.prompts import INTENT_SYSTEM_PROMPT
from backend.agents.types import IntentResult

logger = logging.getLogger(__name__)


class IntentAgent:
    """Detects user intent and extracts entities before any tool call."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        context_info = ""
        if context:
            context_type = context.get("context_type")
            if not context_type:
                if "player_id" in context:
                    context_type = "player"
                elif "team_id" in context and "league_id" in context:
                    context_type = "league_team"
                elif "team_id" in context:
                    context_type = "team"
                elif "match_id" in context or "fixture_id" in context:
                    context_type = "match"
                elif "league_id" in context:
                    context_type = "league"

            if context_type == "match":
                match_id = context.get("match_id") or context.get("fixture_id")
                league_id = context.get("league_id")
                details = f"match #{match_id}"
                if league_id:
                    details += f" in league #{league_id}"
                context_info = f"\n\nContext: User is asking about {details}."
            elif context_type == "league":
                context_info = f"\n\nContext: User is asking about league #{context.get('league_id')}."
            elif context_type == "team":
                context_info = f"\n\nContext: User is asking about team #{context.get('team_id')}."
            elif context_type == "league_team":
                context_info = (
                    f"\n\nContext: User is asking about team #{context.get('team_id')} "
                    f"in league #{context.get('league_id')}."
                )
            elif context_type == "player":
                context_info = f"\n\nContext: User is asking about player #{context.get('player_id')}."
            else:
                context_info = f"\n\nContext: {json.dumps(context, ensure_ascii=True)}"

        enriched_message = user_message + context_info

        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": enriched_message},
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
            if intent == "match_analysis":
                intent = "analyse_rencontre"
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
