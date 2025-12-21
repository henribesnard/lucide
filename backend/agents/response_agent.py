import json
import logging
import re
from typing import Dict, Optional, Any

from backend.agents.types import AnalysisResult, IntentResult
from backend.llm.client import LLMClient
from backend.prompts import ANSWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
SEASON_HINT_PATTERN = re.compile(r"Season:\s*(\d{4})")


def _extract_season_hint(data_points: list[str]) -> Optional[int]:
    for item in data_points:
        match = SEASON_HINT_PATTERN.search(str(item))
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None


class ResponseAgent:
    """Produces the final user-facing answer using the structured analysis."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(
        self,
        user_message: str,
        intent: IntentResult,
        analysis: AnalysisResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        season_hint = _extract_season_hint(analysis.data_points)
        messages = [
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {
                "role": "system",
                "content": f"Intent detecte: {intent.intent}. Entites: {json.dumps(intent.entities, ensure_ascii=False)}",
            },
            {
                "role": "system",
                "content": (
                    f"Context payload: {json.dumps(context, ensure_ascii=True)}"
                    if context else "Context payload: none"
                ),
            },
            {"role": "system", "content": f"Brief: {analysis.brief}"},
            {"role": "system", "content": f"Data points: {json.dumps(analysis.data_points, ensure_ascii=False)}"},
            {"role": "system", "content": f"Gaps: {json.dumps(analysis.gaps, ensure_ascii=False)}"},
            {"role": "system", "content": f"Safety: {json.dumps(analysis.safety_notes, ensure_ascii=False)}"},
        ]
        if season_hint:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"Season used in tools: {season_hint}. "
                        "Use this exact year in the answer and do not convert it to a range."
                    ),
                }
            )

        try:
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.35,
                max_tokens=650,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"Response agent failed: {exc}", exc_info=True)
            return (
                "Je n'ai pas pu generer la reponse finale. Merci de reformuler ou de reessayer plus tard."
            )
