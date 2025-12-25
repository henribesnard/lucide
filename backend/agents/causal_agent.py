"""
Causal agent wrapper for the causal engine.
"""

from typing import Dict, Optional, List
import logging

from backend.agents.types import IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.causal.engine import CausalEngine, CausalAnalysisResult

logger = logging.getLogger(__name__)


class CausalAgent:
    """Decides when to run causal analysis and handles caching hooks."""

    def __init__(self, context_agent=None, enable_cache: bool = True):
        self.context_agent = context_agent
        self.enable_cache = enable_cache

    def should_run(
        self,
        question: str,
        intent: IntentResult,
        tool_results: List[ToolCallResult],
    ) -> bool:
        if intent.intent in {"analyse_rencontre", "match_analysis"}:
            return True
        lowered = question.lower()
        causal_keywords = [
            "pourquoi",
            "cause",
            "raison",
            "explique",
            "expliquer",
            "impact",
            "influence",
            "que se passerait",
            "si ",
        ]
        if any(k in lowered for k in causal_keywords):
            return True
        has_stats = any(tr.name == "fixture_statistics" for tr in tool_results)
        return has_stats and "analyse" in lowered

    async def run(
        self,
        question: str,
        intent: IntentResult,
        tool_results: List[ToolCallResult],
        llm_client: LLMClient,
        context: Optional[Dict] = None,
        language: str = "fr",
    ) -> Optional[CausalAnalysisResult]:
        engine = CausalEngine(llm_client)
        result = await engine.analyze(question, intent, tool_results, context=context, language=language)

        if self.enable_cache:
            self._update_cache(tool_results, result)

        return result

    def _update_cache(self, tool_results: List[ToolCallResult], result: CausalAnalysisResult) -> None:
        if not self.context_agent:
            return
        fixture_id = _extract_fixture_id(tool_results)
        if not fixture_id:
            return
        payload = result.to_payload()
        payload["version"] = "1.0"
        try:
            updated = self.context_agent.update_causal_cache(fixture_id, payload)
            if updated:
                logger.info("Causal cache updated for fixture %s", fixture_id)
        except Exception as exc:
            logger.warning("Failed to update causal cache: %s", exc)


def _extract_fixture_id(tool_results: List[ToolCallResult]) -> Optional[int]:
    for tr in tool_results:
        if tr.name == "fixtures_search" and isinstance(tr.output, dict):
            fixtures = tr.output.get("fixtures") or []
            if fixtures:
                fixture_id = fixtures[0].get("fixture_id")
                if fixture_id:
                    return fixture_id
    return None
