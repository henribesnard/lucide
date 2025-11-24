import json
import logging

from backend.agents.types import AnalysisResult, IntentResult
from backend.llm.client import LLMClient
from backend.prompts import ANSWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ResponseAgent:
    """Produces the final user-facing answer using the structured analysis."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(
        self,
        user_message: str,
        intent: IntentResult,
        analysis: AnalysisResult,
    ) -> str:
        messages = [
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {
                "role": "system",
                "content": f"Intent detecte: {intent.intent}. Entites: {json.dumps(intent.entities, ensure_ascii=False)}",
            },
            {"role": "system", "content": f"Brief: {analysis.brief}"},
            {"role": "system", "content": f"Data points: {json.dumps(analysis.data_points, ensure_ascii=False)}"},
            {"role": "system", "content": f"Gaps: {json.dumps(analysis.gaps, ensure_ascii=False)}"},
            {"role": "system", "content": f"Safety: {json.dumps(analysis.safety_notes, ensure_ascii=False)}"},
        ]

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
