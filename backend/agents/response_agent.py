import json
import logging
import re
from typing import Dict, Optional, Any, Literal

from backend.agents.types import AnalysisResult, IntentResult
from backend.llm.client import LLMClient
from backend.prompts import ANSWER_SYSTEM_PROMPT
from backend.prompts_i18n import get_response_prompt

logger = logging.getLogger(__name__)
Language = Literal["fr", "en"]
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
        language: Language = "fr",
    ) -> str:
        season_hint = _extract_season_hint(analysis.data_points)

        # Format context for prompt
        context_str = f"""
Intent: {intent.intent}
Entities: {json.dumps(intent.entities, ensure_ascii=False)}
Context: {json.dumps(context, ensure_ascii=True) if context else "none"}

Brief: {analysis.brief}

Data points:
{json.dumps(analysis.data_points, ensure_ascii=False)}

Gaps: {json.dumps(analysis.gaps, ensure_ascii=False)}
Safety notes: {json.dumps(analysis.safety_notes, ensure_ascii=False)}
"""

        if analysis.causal_summary:
            context_str += f"\n\nCausal analysis:\n{analysis.causal_summary}"

        if season_hint:
            context_str += f"\n\nSeason: {season_hint} (use this exact year, do not convert to range)"

        # Build multilingual prompt
        prompt = get_response_prompt(
            question=user_message,
            context=context_str,
            language=language
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            response = await self.llm.chat_completion(
                messages=messages,
                temperature=0.35,
                max_tokens=2000,  # Increased from 650 to allow complete analyses
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"Response agent failed: {exc}", exc_info=True)
            if language == "en":
                return "I could not generate the final answer. Please rephrase or try again later."
            else:
                return "Je n'ai pas pu generer la reponse finale. Merci de reformuler ou de reessayer plus tard."
