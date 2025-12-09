import json
import logging
import re
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


def _repair_json(content: str) -> str:
    """
    Best-effort repair of common JSON issues returned by the LLM:
    - Trailing commas before closing braces/brackets
    - Unbalanced quotes/braces/brackets
    """
    # Remove trailing commas
    content = re.sub(r",(\s*[}\]])", r"\1", content)

    # Balance quotes
    if content.count('"') % 2 != 0:
        content += '"'

    # Balance braces
    open_braces = content.count("{")
    close_braces = content.count("}")
    if open_braces > close_braces:
        content += "}" * (open_braces - close_braces)

    # Balance brackets
    open_brackets = content.count("[")
    close_brackets = content.count("]")
    if open_brackets > close_brackets:
        content += "]" * (open_brackets - close_brackets)

    return content


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
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                )
            except Exception as exc:
                logger.warning(f"Analysis agent json mode failed, retrying without format: {exc}")
                response = await self.llm.chat_completion(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1000,
                )
            content = response.choices[0].message.content or "{}"
            content = content.strip()

            if content.startswith("```"):
                match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
                if match:
                    content = match.group(1)

            try:
                payload = json.loads(content)
            except json.JSONDecodeError as exc:
                logger.warning(f"JSON parsing failed: {exc}, attempting repair")
                try:
                    repaired = _repair_json(content)
                    payload = json.loads(repaired)
                    logger.info("JSON repair successful")
                except json.JSONDecodeError as exc2:
                    logger.error(f"JSON repair failed: {exc2}")
                    logger.error(f"Raw content: {content}")
                    payload = {
                        "brief": "Desole, je n'ai pas pu generer une analyse structuree. Voici un resume minimal.",
                        "data_points": [],
                        "gaps": ["Erreur lors de la generation de l'analyse"],
                        "safety_notes": [],
                    }
            return AnalysisResult(
                brief=payload.get("brief", ""),
                data_points=payload.get("data_points", []) if isinstance(payload.get("data_points", []), list) else [str(payload.get("data_points"))],
                gaps=payload.get("gaps", []) if isinstance(payload.get("gaps", []), list) else [str(payload.get("gaps"))],
                safety_notes=payload.get("safety_notes", []) if isinstance(payload.get("safety_notes", []), list) else [str(payload.get("safety_notes"))],
            )
        except Exception as exc:
            logger.error(f"Analysis agent failed: {exc}", exc_info=True)
            return AnalysisResult(
                brief=assistant_notes or "Analyse indisponible.",
                data_points=[f"Intent: {intent.intent}", f"Entites: {intent.entities}"],
                gaps=["Impossible de structurer les donnees renvoyees"],
                safety_notes=[],
            )
