import json
import logging
import re
from typing import Any, Dict, List, Optional

from backend.agents.types import AnalysisResult, IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.prompts import ANALYSIS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def _extract_season_hint(tool_results: List[ToolCallResult]) -> Optional[int]:
    for tr in tool_results:
        output = tr.output
        if isinstance(output, dict):
            season = output.get("season")
            if season is not None:
                try:
                    return int(season)
                except (TypeError, ValueError):
                    pass
        if isinstance(tr.arguments, dict):
            season = tr.arguments.get("season")
            if season is not None:
                try:
                    return int(season)
                except (TypeError, ValueError):
                    pass
    return None


def _extract_score_hint(tool_results: List[ToolCallResult]) -> Optional[Dict[str, str]]:
    for tr in tool_results:
        if tr.name != "fixtures_search":
            continue
        output = tr.output
        if not isinstance(output, dict):
            continue
        fixtures = output.get("fixtures") or []
        if not fixtures:
            continue
        fx = fixtures[0]
        home = fx.get("home") or {}
        away = fx.get("away") or {}
        home_name = home.get("name")
        away_name = away.get("name")
        home_goals = home.get("goals")
        away_goals = away.get("goals")
        status = fx.get("status_code") or fx.get("status")
        if home_name and away_name and home_goals is not None and away_goals is not None:
            label = "Score actuel"
            if status in {"FT", "AET", "PEN"}:
                label = "Score final"
            return {
                "score": f"{label}: {home_name} {home_goals} - {away_goals} {away_name}",
                "status": f"Statut: {status}" if status else "",
            }
    return None


def _compact_output(output: Any, tool_name: Optional[str] = None) -> Any:
    """
    Compacte les outputs pour réduire la taille, mais garde les données critiques intactes.
    Utilise une logique intelligente basée sur le type de données et l'intent.

    Limits par type de données:
    - Lineups: 30 joueurs (compos complètes)
    - Events: 25 événements (match complet)
    - H2H: 10 matchs (historique substantiel)
    - Standings: 10 équipes (top + contexte)
    - Top performers: 15 joueurs (large contexte)
    - Fixtures: 10 matchs (contexte suffisant)
    - Default: 5 éléments
    """
    if isinstance(output, list):
        # Détecter le type de liste et appliquer la limite appropriée
        if output and isinstance(output[0], dict):
            first_item_keys = set(output[0].keys())

            # Players/Lineups: garde 30 éléments
            if 'player' in first_item_keys or ('name' in first_item_keys and 'number' in first_item_keys):
                return output[:30]

            # Events: garde 25 événements
            if 'time' in first_item_keys and 'team' in first_item_keys and 'type' in first_item_keys:
                return output[:25]

            # Standings: garde 10 équipes
            if 'rank' in first_item_keys and 'points' in first_item_keys:
                return output[:10]

            # Top performers (scorers, assists): garde 15
            if tool_name in ('top_scorers', 'top_assists', 'top_yellow_cards', 'top_red_cards'):
                return output[:15]

            # H2H fixtures: garde 10 matchs
            if 'fixture' in first_item_keys and 'teams' in first_item_keys:
                return output[:10]

        # Default: limite à 5
        return output[:5]

    if isinstance(output, dict):
        compacted: Dict[str, Any] = {}
        for key, value in output.items():
            if isinstance(value, list):
                # Appliquer la même logique aux listes imbriquées
                if value and isinstance(value[0], dict):
                    first_item_keys = set(value[0].keys())

                    # Players/Lineups
                    if 'player' in first_item_keys or ('name' in first_item_keys and 'number' in first_item_keys):
                        compacted[key] = value[:30]
                    # Events
                    elif 'time' in first_item_keys and 'team' in first_item_keys and 'type' in first_item_keys:
                        compacted[key] = value[:25]
                    # Standings
                    elif 'rank' in first_item_keys and 'points' in first_item_keys:
                        compacted[key] = value[:10]
                    # Fixtures/H2H
                    elif 'fixture' in first_item_keys and 'teams' in first_item_keys:
                        compacted[key] = value[:10]
                    # Default
                    else:
                        compacted[key] = value[:5]
                else:
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
        context: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        clean_results = [
            {
                "tool": tr.name,
                "arguments": tr.arguments,
                "output": _compact_output(tr.output, tr.name),
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
                "content": (
                    f"Context payload: {json.dumps(context, ensure_ascii=True)}"
                    if context else "Context payload: none"
                ),
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
            data_points = payload.get("data_points", [])
            if not isinstance(data_points, list):
                data_points = [str(data_points)]
            score_hint = _extract_score_hint(tool_results)
            if score_hint and not any("score" in str(item).lower() for item in data_points):
                data_points.insert(0, score_hint["score"])
                if score_hint.get("status") and not any(str(item).lower().startswith("statut") for item in data_points):
                    data_points.insert(1, score_hint["status"])
            season_hint = _extract_season_hint(tool_results)
            if season_hint is not None:
                season_tag = f"Season: {season_hint}"
                if not any(str(item).startswith("Season:") for item in data_points):
                    data_points.insert(0, season_tag)
            return AnalysisResult(
                brief=(
                    score_hint["score"]
                    if score_hint and intent.intent in {"result_final", "stats_final", "events_summary"}
                    else payload.get("brief", "")
                ),
                data_points=data_points,
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
