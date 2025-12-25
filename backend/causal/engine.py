"""
Integration engine for causal analysis (rules + metrics + LLM synthesis).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Literal
import json
import logging
import re

from backend.agents.types import ToolCallResult, IntentResult
from backend.llm.client import LLMClient
from backend.prompts_i18n import get_causal_analysis_prompt
from .calculator import CausalCalculator
from .prompts import QuestionType, get_prompt_for_question
from .rules import CausalRuleEngine, prepare_match_data_for_rules

logger = logging.getLogger(__name__)
Language = Literal["fr", "en"]


@dataclass
class CausalAnalysisResult:
    question_type: QuestionType
    rule_findings: List[Dict[str, Any]]
    calculated_metrics: Dict[str, Any]
    llm_analysis: str
    confidence_overall: str

    def to_payload(self) -> Dict[str, Any]:
        return {
            "question_type": self.question_type.value,
            "rule_findings": self.rule_findings,
            "calculated_metrics": self.calculated_metrics,
            "confidence_overall": self.confidence_overall,
        }


class CausalEngine:
    """Combine rules + metrics + LLM to generate causal explanations."""

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.calculator = CausalCalculator()
        self.rules_engine = CausalRuleEngine()

    async def analyze(
        self,
        question: str,
        intent: IntentResult,
        tool_results: List[ToolCallResult],
        context: Optional[Dict[str, Any]] = None,
        language: Language = "fr",
    ) -> CausalAnalysisResult:
        fixture = _get_tool_output(tool_results, "fixtures_search") or {}
        fixture_summary = _first_fixture(fixture)
        stats_payload = _get_tool_output(tool_results, "fixture_statistics") or {}
        stats_list = stats_payload.get("statistics") or []
        events_payload = _get_tool_output(tool_results, "fixture_events") or {}
        events = events_payload.get("events") or []

        team_id, team_name = self._infer_target_team(question, intent, context, fixture_summary, stats_list)

        match_data = prepare_match_data_for_rules(
            fixture_summary or {},
            stats_list,
            events,
            team_id=team_id,
            team_name=team_name,
        )

        metrics = self._calculate_metrics(match_data, stats_list, tool_results, fixture_summary)
        match_data.update(
            {
                "xg_estime": metrics.get("xg", {}).get("xg_estime"),
                "fatigue_score": metrics.get("fatigue", {}).get("fatigue_score"),
                "key_absences": metrics.get("key_absences", {}).get("count"),
            }
        )

        rule_findings = self.rules_engine.analyze(match_data)
        question_type = self._classify_question(question)
        prompt = self._build_prompt(question, question_type, match_data, stats_list, rule_findings, metrics, language)
        llm_analysis = await self._call_llm(prompt, language)
        confidence = self._assess_confidence(rule_findings, metrics)

        return CausalAnalysisResult(
            question_type=question_type,
            rule_findings=rule_findings,
            calculated_metrics=metrics,
            llm_analysis=llm_analysis,
            confidence_overall=confidence,
        )

    def _classify_question(self, question: str) -> QuestionType:
        lowered = question.lower()
        if any(k in lowered for k in ["pourquoi", "cause", "raison", "explique"]):
            return QuestionType.CAUSAL_WHY
        if any(k in lowered for k in ["si ", "que se passerait", "what if", "if "]):
            return QuestionType.CAUSAL_WHAT_IF
        if any(k in lowered for k in ["compare", "versus", "vs", "comparaison"]):
            return QuestionType.CAUSAL_COMPARE
        return QuestionType.HYBRID

    def _build_prompt(
        self,
        question: str,
        question_type: QuestionType,
        match_data: Dict[str, Any],
        stats_list: List[Dict[str, Any]],
        rule_findings: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        language: Language = "fr",
    ) -> str:
        enriched_context = self._format_context(rule_findings, metrics)
        match_json = json.dumps(match_data, indent=2, ensure_ascii=True)
        stats_json = json.dumps(stats_list, indent=2, ensure_ascii=True)

        # Use multilingual causal analysis prompt
        return get_causal_analysis_prompt(
            question=question,
            match_data=match_json,
            stats=stats_json,
            enriched_context=enriched_context,
            language=language
        )

    def _format_context(self, findings: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        lines: List[str] = []
        if findings:
            lines.append("Rule findings:")
            for idx, f in enumerate(findings, 1):
                lines.append(f"{idx}. {f.get('cause')} (confidence: {f.get('confidence')})")
                lines.append(f"   Mechanism: {f.get('mechanism')}")
        else:
            lines.append("Rule findings: none")

        if metrics:
            lines.append("Metrics:")
            if "xg" in metrics:
                xg = metrics["xg"]
                lines.append(f"- xG: {xg.get('xg_estime')} delta={xg.get('delta')}")
                lines.append(f"  interpretation: {xg.get('interpretation')}")
            if "fatigue" in metrics:
                fatigue = metrics["fatigue"]
                lines.append(f"- fatigue_score: {fatigue.get('fatigue_score')}")
                lines.append(f"  matches_7d: {fatigue.get('matches_7d')}, days_rest: {fatigue.get('days_rest')}")
            if "key_absences" in metrics:
                ka = metrics["key_absences"]
                lines.append(f"- key_absences: {ka.get('count')}")
        return "\n".join(lines)

    def _calculate_metrics(
        self,
        match_data: Dict[str, Any],
        stats_list: List[Dict[str, Any]],
        tool_results: List[ToolCallResult],
        fixture_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {}

        team_stats_map = _stats_for_team(stats_list, match_data.get("team_id"), match_data.get("team_name"))
        if team_stats_map is not None:
            goals = int(match_data.get("goals") or 0)
            metrics["xg"] = self.calculator.xg_analysis(team_stats_map, goals)

        fatigue = self._fatigue_metrics(match_data.get("team_id"), tool_results, fixture_summary)
        if fatigue:
            metrics["fatigue"] = fatigue

        key_absences = self._key_absences(match_data.get("team_name"), tool_results)
        if key_absences:
            metrics["key_absences"] = key_absences

        return metrics

    def _fatigue_metrics(
        self,
        team_id: Optional[int],
        tool_results: List[ToolCallResult],
        fixture_summary: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not team_id:
            return None
        fixtures = []
        for tr in tool_results:
            if tr.name == "team_last_fixtures" and tr.arguments.get("team_id") == team_id:
                payload = tr.output if isinstance(tr.output, dict) else {}
                fixtures = payload.get("fixtures") or []
                break
        if not fixtures:
            return None
        reference_date = _fixture_date(fixture_summary)
        return self.calculator.fatigue_analysis(fixtures, reference_date)

    def _key_absences(self, team_name: Optional[str], tool_results: List[ToolCallResult]) -> Optional[Dict[str, Any]]:
        if not team_name:
            return None
        injuries = _get_tool_output(tool_results, "injuries") or {}
        injury_list = injuries.get("injuries") or []
        top_scorers = (_get_tool_output(tool_results, "top_scorers") or {}).get("top_scorers") or []
        top_assists = (_get_tool_output(tool_results, "top_assists") or {}).get("top_assists") or []

        key_players = {p.get("name") for p in top_scorers + top_assists if p.get("name")}
        missing = [
            i for i in injury_list
            if i.get("team") and i.get("player")
            and str(i.get("team")).lower() == team_name.lower()
            and i.get("player") in key_players
        ]
        return {"count": len(missing), "players": [m.get("player") for m in missing]}

    async def _call_llm(self, prompt: str, language: Language = "fr") -> str:
        system_message = {
            "fr": "Tu es un analyste football expert et méthodique.",
            "en": "You are an expert and methodical football analyst."
        }
        messages = [
            {"role": "system", "content": system_message.get(language, system_message["fr"])},
            {"role": "user", "content": prompt},
        ]
        response = await self.llm.chat_completion(messages=messages, temperature=0.2, max_tokens=700)
        return (response.choices[0].message.content or "").strip()

    def _assess_confidence(self, findings: List[Dict[str, Any]], metrics: Dict[str, Any]) -> str:
        if not findings and not metrics:
            return "low"
        high = sum(1 for f in findings if f.get("confidence") == "high")
        if high >= 2:
            return "high"
        if high >= 1 or len(findings) >= 2:
            return "medium"
        return "low"

    def _infer_target_team(
        self,
        question: str,
        intent: IntentResult,
        context: Optional[Dict[str, Any]],
        fixture_summary: Dict[str, Any],
        stats_list: List[Dict[str, Any]],
    ) -> tuple[Optional[int], Optional[str]]:
        # 1) From context
        if context:
            if context.get("team_id"):
                return context.get("team_id"), context.get("team_name")
            if context.get("team"):
                return None, context.get("team")

        # 2) From intent entities
        if intent.entities.get("team_id"):
            return intent.entities.get("team_id"), intent.entities.get("team")

        # 3) From question + fixture names
        home = (fixture_summary.get("home") or {}).get("name")
        away = (fixture_summary.get("away") or {}).get("name")
        if home and _mentions(question, home):
            return (fixture_summary.get("home") or {}).get("id"), home
        if away and _mentions(question, away):
            return (fixture_summary.get("away") or {}).get("id"), away

        # 4) From stats list (first team)
        if stats_list:
            first = stats_list[0]
            return first.get("team_id"), first.get("team")

        return None, None


def _get_tool_output(tool_results: List[ToolCallResult], name: str) -> Optional[Dict[str, Any]]:
    for tr in tool_results:
        if tr.name == name and isinstance(tr.output, dict):
            return tr.output
    return None


def _first_fixture(payload: Dict[str, Any]) -> Dict[str, Any]:
    fixtures = payload.get("fixtures") or []
    if fixtures:
        return fixtures[0]
    return payload


def _fixture_date(fixture: Dict[str, Any]) -> Optional[str]:
    date = fixture.get("date")
    if date:
        return date
    fixture_block = fixture.get("fixture") or {}
    return fixture_block.get("date")


def _mentions(text: str, name: str) -> bool:
    pattern = re.compile(r"\b" + re.escape(name.lower()) + r"\b")
    return bool(pattern.search(text.lower()))


def _stats_for_team(
    stats_list: List[Dict[str, Any]],
    team_id: Optional[int],
    team_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not stats_list:
        return None
    for stat in stats_list:
        if team_id and stat.get("team_id") == team_id:
            return stat.get("stats") or {}
        if team_name and stat.get("team") and str(stat.get("team")).lower() == team_name.lower():
            return stat.get("stats") or {}
    return stats_list[0].get("stats") or {}
