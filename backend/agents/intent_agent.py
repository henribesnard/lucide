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
            data_required_intents = {
                "analyse_rencontre",
                "score_live",
                "stats_live",
                "events_live",
                "players_live",
                "lineups_live",
                "result_final",
                "stats_final",
                "events_summary",
                "players_performance",
                "prediction_global",
                "form_analysis",
                "h2h_analysis",
                "stats_comparison",
                "injuries_impact",
                "probable_lineups",
                "odds_analysis",
                "standings",
                "classement_ligue",
                "top_performers",
                "top_scorers",
                "top_assists",
                "top_cartons",
                "top_yellow_cards",
                "top_red_cards",
                "team_stats",
                "next_fixtures",
                "results",
                "calendrier_matchs",
                "calendrier_ligue_saison",
                "calendrier_equipe",
                "matchs_live_filtre",
                "prochains_ou_derniers_matchs",
                "detail_fixture",
                "chronologie_match",
                "compositions_match",
                "stats_equipes_match",
                "stats_joueurs_match",
                "journees_competition",
                "stats_equipe_saison",
                "stats_joueur",
            }
            if intent in data_required_intents:
                needs_data = True
            if intent == "info_generale":
                needs_data = False
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
