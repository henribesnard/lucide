import json
import logging
from typing import List, Tuple, Optional
from datetime import datetime

from backend.api.football_api import FootballAPIClient
from backend.agents.types import IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.prompts import TOOL_SYSTEM_PROMPT
from backend.tools.football import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)


class ToolAgent:
    """Handles DeepSeek function calling and executes the mapped tools."""

    def __init__(
        self,
        llm: LLMClient,
        api_client: FootballAPIClient,
        context_agent: Optional["ContextAgent"] = None,
        max_iterations: int = 3
    ):
        self.llm = llm
        self.api_client = api_client
        self.context_agent = context_agent
        self.max_iterations = max_iterations

    async def _force_critical_tools_for_match_analysis(
        self,
        intent: IntentResult,
        tool_results: List[ToolCallResult],
    ) -> List[ToolCallResult]:
        """
        If analyse_rencontre is missing critical data, force the execution of must-have tools.
        """
        if intent.intent != "analyse_rencontre":
            return tool_results

        available_tools = {tr.name for tr in tool_results}
        required = {"fixtures_search", "team_last_fixtures", "standings", "team_statistics", "head_to_head"}
        missing_required = required - available_tools
        if not missing_required:
            return tool_results

        # Gather team ids and fixture/league info from previous tool results
        team_ids: List[int] = []
        fixture_id: Optional[int] = None
        league_id: Optional[int] = intent.entities.get("league_id")
        season: Optional[int] = intent.entities.get("season")

        team_last_fixtures_done = set(
            tr.arguments.get("team_id") for tr in tool_results if tr.name == "team_last_fixtures" and isinstance(tr.arguments, dict)
        )
        team_statistics_done = set(
            tr.arguments.get("team_id") for tr in tool_results if tr.name == "team_statistics" and isinstance(tr.arguments, dict)
        )

        for tr in tool_results:
            if tr.name == "search_team" and isinstance(tr.output, dict):
                teams = tr.output.get("teams") or []
                for t in teams:
                    tid = t.get("id")
                    if tid:
                        team_ids.append(tid)
            if tr.name == "fixtures_search" and isinstance(tr.output, dict):
                fixtures = tr.output.get("fixtures") or []
                if fixtures:
                    fx = fixtures[0]
                    fixture = fx.get("fixture") or {}
                    league = fx.get("league") or {}
                    fixture_id = fixture.get("id") or fixture_id
                    league_id = league_id or league.get("id")
                    season = season or league.get("season")
                    teams_block = fx.get("teams") or {}
                    home_team = teams_block.get("home") or {}
                    away_team = teams_block.get("away") or {}
                    for tid in [home_team.get("id"), away_team.get("id")]:
                        if tid:
                            team_ids.append(tid)

        if len(team_ids) < 2:
            logger.warning("Force critical tools: not enough teams found; skipping force execution.")
            return tool_results

        # Fallbacks
        now = datetime.utcnow()
        if not season:
            season = now.year if now.month >= 8 else now.year - 1
        if not league_id and fixture_id:
            # try to recover from intent default league mapping (Premier League 39) as last resort
            league_id = intent.entities.get("league_id") or 39

        # Force executions using execute_tool
        # 1. team_last_fixtures for both teams if missing
        for tid in team_ids[:2]:
            if tid in team_last_fixtures_done:
                continue
            logger.info(f"Force-executing team_last_fixtures for team {tid}")
            result = await execute_tool(self.api_client, "team_last_fixtures", {"team_id": tid, "count": 5})
            tool_results.append(
                ToolCallResult(
                    name="team_last_fixtures",
                    arguments={"team_id": tid, "count": 5},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 2. standings
        if "standings" not in available_tools and league_id and season:
            logger.info(f"Force-executing standings for league {league_id}, season {season}")
            result = await execute_tool(
                self.api_client,
                "standings",
                {"league_id": league_id, "season": season},
            )
            tool_results.append(
                ToolCallResult(
                    name="standings",
                    arguments={"league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 3. head_to_head
        if "head_to_head" not in available_tools:
            logger.info(f"Force-executing head_to_head for teams {team_ids[0]} vs {team_ids[1]}")
            result = await execute_tool(
                self.api_client,
                "head_to_head",
                {"team1_id": team_ids[0], "team2_id": team_ids[1]},
            )
            tool_results.append(
                ToolCallResult(
                    name="head_to_head",
                    arguments={"team1_id": team_ids[0], "team2_id": team_ids[1]},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 4. team_statistics for both teams
        for tid in team_ids[:2]:
            if tid in team_statistics_done or not league_id or not season:
                continue
            logger.info(f"Force-executing team_statistics for team {tid}")
            result = await execute_tool(
                self.api_client,
                "team_statistics",
                {"team_id": tid, "league_id": league_id, "season": season},
            )
            tool_results.append(
                ToolCallResult(
                    name="team_statistics",
                    arguments={"team_id": tid, "league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        return tool_results

    async def run(self, user_message: str, intent: IntentResult) -> Tuple[List[ToolCallResult], str]:
        league_mapping = (
            "Mapping ligues vers IDs: "
            "Ligue 1=61; Premier League=39; La Liga=140; Bundesliga=78; Serie A=135; "
            "Ligue des Champions=2; Europa League=3."
        )
        intent_guidance = {
            "classement_ligue": "Utilise le tool standings avec league_id et season (convertis le nom de ligue via le mapping).",
            "live_scores": "Si aucune ligue precisee, utilise live_fixtures; sinon fixtures_search live='all' + league_id.",
            "prochain_match_equipe": "Utilise search_team puis team_next_fixtures (count=1 par defaut).",
            "calendrier_matchs": (
                "Resous league -> league_id meme pour '1ere division <pays>'. "
                "Si date absente, prends aujourd'hui; season par defaut = saison en cours. "
                "Appelle fixtures_by_date ou fixtures_search avec league_id/date/season/status quand dispo."
            ),
            "analyse_rencontre": (
                "Identifie les 2 equipes (search_team) puis la fixture cible (fixtures_search/fixtures_by_date). "
                "Ensuite, collecte un bouquet complet: team_last_fixtures pour chaque equipe (forme recente), standings (classement), "
                "team_statistics pour chaque equipe, head_to_head (confrontations), injuries (blesses/suspendus), "
                "fixture_lineups et fixture_statistics si fixture_id connu, et predictions/odds si pertinent. "
                "Ne te contente pas d'un seul appel: enchaine les tool_calls necessaires dans la meme reponse."
            ),
            "stats_equipe_saison": (
                "Resous team -> team_id via search_team puis appelle team_statistics avec league_id + season (defaut saison actuelle)."
            ),
            "stats_joueur": (
                "Utilise search_player pour obtenir player_id; season par defaut = saison en cours. "
                "Le tool search_player suffit pour les stats globales."
            ),
            "top_performers": "Utilise top_scorers ou top_assists selon la demande.",
            "top_cartons": "Utilise top_yellow_cards ou top_red_cards selon jaunes/rouges.",
            "calendrier_ligue_saison": "Utilise fixtures_search avec league_id + season (+ from/to/round/status/timezone si fourni).",
            "calendrier_equipe": "Utilise search_team puis fixtures_search avec team_id (+ season/from/to/status/timezone).",
            "matchs_live_filtre": "Utilise fixtures_search avec live='all' et filtres league_id ou team_id si donnes.",
            "prochains_ou_derniers_matchs": "Utilise fixtures_search avec next ou last (plus league_id/team_id si dispo).",
            "detail_fixture": "Si fixture_id fourni, enchaine fixture_events + fixture_lineups + fixture_statistics + fixture_players selon besoin.",
            "chronologie_match": "fixture_events avec fixture_id (filtres team_id/player_id/type si fournis).",
            "compositions_match": "fixture_lineups avec fixture_id (team_id optionnel).",
            "stats_equipes_match": "fixture_statistics avec fixture_id (team_id optionnel).",
            "stats_joueurs_match": "fixture_players avec fixture_id (team_id optionnel).",
            "journees_competition": "fixture_rounds avec league_id et season (current=true si demande de journee actuelle).",
            "referentiel_pays": "Appelle countries avec filtres name/code/search si fournis.",
            "referentiel_ligues": "Appelle leagues avec filtres id/name/country/code/type/current/season/search/last.",
            "saisons_disponibles": "Appelle league_seasons.",
            "timezones_disponibles": "Appelle timezones.",
            "info_equipe": "Utilise teams (ou search_team) avec league/season/country/code/venue/search.",
            "saisons_equipe": "team_seasons avec team_id (resoudre via search_team si nom).",
            "effectif_equipe": "players_squads avec team_id (resoudre via search_team).",
            "equipes_dun_joueur": "players_squads avec player_id (resoudre via search_player).",
            "profil_joueur": "player_profile avec player_id ou search.",
            "stats_joueur_saison_detail": "player_statistics avec player_id ou player_name + season (+league/team).",
            "parcours_equipes_joueur": "players_squads avec player_id pour obtenir ses equipes (ou player_teams si disponible).",
            "blessures_precises": "injuries avec league_id/season/fixture_id/team_id/player_id/date/timezone.",
            "blessures": "injuries avec league_id/season/team_id/fixture_id/player_id/date/timezone.",
            "indisponibilites_historiques": "sidelined avec player_id ou coach_id.",
            "odds_live": "odds_live avec fixture_id prioritaire (sinon league_id/bet_id).",
            "odds_referentiels": "odds_bookmakers pour la liste des bookmakers, odds_bets pour les types de paris, odds_mapping pour la couverture.",
            "api_status": "api_status pour connaitre le quota et la sante de l'API-Football.",
            "transferts": "transfers avec player_id ou team_id.",
            "palmares": "trophies avec player_id ou coach_id.",
            "coach_info": "coaches avec coach_id/team_id/search.",
            "stade_info": "venues avec venue_id/name/city/country/search.",
        }

        messages = [
            {"role": "system", "content": TOOL_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"Intent cible: {intent.intent}. Entites: {intent.entities}. "
                "Si needs_data est False, reponds directement par une courte note sans tool.",
            },
            {"role": "system", "content": league_mapping},
            {
                "role": "system",
                "content": intent_guidance.get(
                    intent.intent,
                    "Choisis les tools les plus pertinents. Utilise le mapping des ligues quand une ligue est mentionnee.",
                ),
            },
            {"role": "user", "content": user_message},
        ]

        tool_results: List[ToolCallResult] = []
        assistant_notes = ""
        conversation = list(messages)

        for _ in range(self.max_iterations):
            try:
                response = await self.llm.chat_completion(
                    messages=conversation,
                    tools=TOOL_DEFINITIONS,
                    temperature=0.0,
                    max_tokens=1500,
                )
            except Exception as exc:
                logger.error(f"Tool agent LLM call failed: {exc}", exc_info=True)
                assistant_notes = "Impossible d'appeler le modele pour les tools."
                break

            choice = response.choices[0]
            msg = choice.message
            finish_reason = choice.finish_reason

            if finish_reason == "stop":
                assistant_notes = msg.content or ""
                break

            if finish_reason == "tool_calls" and msg.tool_calls:
                # Record assistant intent for traceability
                conversation.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )

                for tool_call in msg.tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        arguments = {}

                    logger.info(f"Executing tool {tool_call.function.name} with args {arguments}")

                    # Special handling for analyze_match tool
                    if tool_call.function.name == "analyze_match" and self.context_agent:
                        fixture_id = arguments.get("fixture_id")
                        bet_type = arguments.get("bet_type")

                        if not fixture_id:
                            result = {"error": "fixture_id is required for analyze_match"}
                        else:
                            try:
                                # Get match context (from cache or fresh)
                                context_data = await self.context_agent.get_match_context(fixture_id)
                                context = context_data["context"]

                                # If bet_type specified, return specific analysis
                                if bet_type:
                                    analysis = context.analyses.get(bet_type)
                                    if analysis:
                                        result = {
                                            "fixture_id": fixture_id,
                                            "match": f"{context.home_team} vs {context.away_team}",
                                            "bet_type": bet_type,
                                            "indicators": analysis.indicators,
                                            "coverage_complete": analysis.coverage_complete,
                                            "source": context_data["source"],
                                            "api_calls": context_data["api_calls"]
                                        }
                                    else:
                                        result = {"error": f"Bet type '{bet_type}' not found"}
                                else:
                                    # Return all available analyses
                                    result = {
                                        "fixture_id": fixture_id,
                                        "match": f"{context.home_team} vs {context.away_team}",
                                        "league": context.league,
                                        "date": str(context.date) if context.date else None,
                                        "status": context.status,
                                        "available_analyses": list(context.analyses.keys()),
                                        "source": context_data["source"],
                                        "api_calls": context_data["api_calls"]
                                    }
                            except Exception as e:
                                result = {"error": f"Failed to analyze match: {str(e)}"}
                    else:
                        # Standard tool execution
                        result = await execute_tool(self.api_client, tool_call.function.name, arguments)

                    tool_results.append(
                        ToolCallResult(
                            name=tool_call.function.name,
                            arguments=arguments,
                            output=result,
                            error=result.get("error") if isinstance(result, dict) else None,
                        )
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                continue

            assistant_notes = msg.content or ""
            break

        # After LLM loop, force missing critical tools for match analysis if needed
        tool_results = await self._force_critical_tools_for_match_analysis(intent, tool_results)

        return tool_results, assistant_notes
