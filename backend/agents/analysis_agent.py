import json
import logging
from typing import Any, Dict, List

from backend.agents.types import AnalysisResult, IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.prompts import ANALYSIS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _compact_output(output: Any) -> Any:
    if isinstance(output, list):
        return output[:5]
    if isinstance(output, dict):
        compacted: Dict[str, Any] = {}
        for key, value in output.items():
            if isinstance(value, list):
                compacted[key] = value[:5]
            else:
                compacted[key] = value
        return compacted
    return output


class AnalysisAgent:
    """Turns raw tool outputs into a compact structured summary."""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(
        self,
        user_message: str,
        intent: IntentResult,
        tool_results: List[ToolCallResult],
        assistant_notes: str,
    ) -> AnalysisResult:
        clean_results = [
            {
                "tool": tr.name,
                "arguments": tr.arguments,
                "output": _compact_output(tr.output),
                "error": tr.error,
            }
            for tr in tool_results
        ]

        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {
                "role": "system",
                "content": f"Intent: {intent.intent}. Entites: {intent.entities}. Notes outils: {assistant_notes}",
            },
            {
                "role": "system",
                "content": f"Resultats outils (compact): {json.dumps(clean_results, ensure_ascii=False)}",
            },
        ]

        try:
            try:
                response = await self.llm.chat_completion(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=400,
                    response_format={"type": "json_object"},
                )
            except Exception as exc:
                logger.warning(f"Analysis agent json mode failed, retrying without format: {exc}")
                response = await self.llm.chat_completion(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=400,
                )
            payload = json.loads(response.choices[0].message.content or "{}")
            return AnalysisResult(
                brief=payload.get("brief", ""),
                data_points=payload.get("data_points", []) or [],
                gaps=payload.get("gaps", []) or [],
                safety_notes=payload.get("safety_notes", []) or [],
            )
        except Exception as exc:
            logger.error(f"Analysis agent failed: {exc}", exc_info=True)
            return AnalysisResult(
                brief=assistant_notes or "Analyse indisponible.",
                data_points=[f"Intent: {intent.intent}", f"Entites: {intent.entities}"],
                gaps=["Impossible de structurer les donnees renvoyees"],
                safety_notes=[],
            )
