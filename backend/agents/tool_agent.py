import asyncio
import json
import logging
import re
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

from backend.api.football_api import FootballAPIClient
from backend.agents.types import IntentResult, ToolCallResult
from backend.llm.client import LLMClient
from backend.prompts import TOOL_SYSTEM_PROMPT
from backend.tools.football import TOOL_DEFINITIONS, execute_tool
from backend.config import settings

logger = logging.getLogger(__name__)

SEASONAL_TOOLS = {
    "standings",
    "top_scorers",
    "top_assists",
    "top_yellow_cards",
    "top_red_cards",
    "team_statistics",
    "fixture_rounds",
    "player_statistics",
    "injuries",
}

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")
RELATIVE_SEASON_PHRASES = (
    "last season",
    "previous season",
    "last year",
    "previous year",
    "past season",
    "saison derniere",
    "derniere saison",
    "saison precedente",
    "saison passee",
    "annee derniere",
    "l an dernier",
    "lan dernier",
)


def _current_season_year(reference: Optional[datetime] = None) -> int:
    now = reference or datetime.utcnow()
    return now.year if now.month >= 8 else now.year - 1


def _season_from_date(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    try:
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return parsed.year if parsed.month >= 8 else parsed.year - 1
    except Exception:
        return None


def _message_mentions_explicit_year(message: str) -> bool:
    return bool(YEAR_PATTERN.search(message))


def _message_mentions_relative_season(message: str) -> bool:
    lowered = message.lower()
    return any(phrase in lowered for phrase in RELATIVE_SEASON_PHRASES)


def _default_season_for_request(message: str, context: Optional[Dict[str, Any]]) -> Optional[int]:
    if _message_mentions_explicit_year(message) or _message_mentions_relative_season(message):
        return None
    if context:
        match_date = context.get("match_date")
        inferred = _season_from_date(match_date)
        if inferred:
            return inferred
        context_season = context.get("season")
        if isinstance(context_season, int):
            return context_season
    return _current_season_year()


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
        If analyse_rencontre or stats_final is missing critical data, force the execution of must-have tools.
        """
        if intent.intent not in {"analyse_rencontre", "match_analysis", "stats_final", "stats_live"}:
            return tool_results

        logger.info("="*80)
        logger.info("DEBUT FORCE CRITICAL TOOLS FOR MATCH ANALYSIS")
        logger.info(f"Intent: {intent.intent}")
        logger.info(f"Entities: {intent.entities}")

        available_tools = {tr.name for tr in tool_results}
        required = {
            "fixtures_search",
            "team_last_fixtures",
            "team_form_stats",
            "league_type",
            "standings",
            "team_statistics",
            "head_to_head",
            "fixture_lineups",
            "injuries",
            "fixture_rounds",
            "top_scorers",
            "top_assists",
        }
        missing_required = required - available_tools

        logger.info(f"Available tools: {available_tools}")
        logger.info(f"Missing required tools: {missing_required}")
        # Ne pas retourner early car on veut toujours essayer d'enrichir les données
        # if not missing_required:
        #     return tool_results

        # Gather team ids and fixture/league info from previous tool results AND from intent entities
        team_ids: List[int] = []

        # Essayer de récupérer les team_ids depuis les entities du contexte
        if intent.entities.get("home_team_id"):
            team_ids.append(intent.entities["home_team_id"])
        if intent.entities.get("away_team_id"):
            team_ids.append(intent.entities["away_team_id"])

        fixture_id: Optional[int] = intent.entities.get("fixture_id") or intent.entities.get("match_id")
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
                team_wrapper = tr.output.get("team")
                if team_wrapper and isinstance(team_wrapper, dict):
                    # search_team returns {'team': {'team': {...}, 'venue': {...}}}
                    team_data = team_wrapper.get("team")
                    if team_data and isinstance(team_data, dict):
                        tid = team_data.get("id")
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

        logger.info(f"Team IDs discovered: {team_ids}")
        logger.info(f"Fixture ID: {fixture_id}")
        logger.info(f"League ID: {league_id}")
        logger.info(f"Season: {season}")

        # CRITIQUE: Si fixtures_search n'a pas été appelé mais qu'on a 2 équipes, le forcer!
        if "fixtures_search" not in available_tools and len(team_ids) >= 2:
            logger.info(f"FORCING fixtures_search for teams {team_ids[0]} vs {team_ids[1]}")
            # Essayer de trouver le prochain match de team_ids[0], puis vérifier si c'est contre team_ids[1]
            # Utiliser team_id (au lieu de team1_id/team2_id) et next=1
            result = await execute_tool(
                self.api_client,
                "fixtures_search",
                {"team_id": team_ids[0], "next": 1},
            )

            # Vérifier si le match trouvé est bien contre la 2ème équipe
            found_match = False
            if isinstance(result, dict):
                fixtures = result.get("fixtures") or []
                logger.info(f"fixtures_search returned {len(fixtures)} fixtures for team {team_ids[0]}")
                for fx in fixtures:
                    teams_block = fx.get("teams") or {}
                    home_id = (teams_block.get("home") or {}).get("id")
                    away_id = (teams_block.get("away") or {}).get("id")
                    logger.info(f"Checking fixture: home={home_id}, away={away_id}")
                    # Vérifier si les deux équipes sont dans ce match
                    if (home_id in team_ids and away_id in team_ids):
                        found_match = True
                        fixture = fx.get("fixture") or {}
                        league = fx.get("league") or {}
                        fixture_id = fixture.get("id") or fixture_id
                        league_id = league_id or league.get("id")
                        season = season or league.get("season")
                        logger.info(f"MATCH FOUND! fixture_id={fixture_id}, league_id={league_id}, season={season}")
                        break

            # Si pas trouvé avec team_ids[0], essayer avec team_ids[1]
            if not found_match:
                logger.info(f"Match not found with team {team_ids[0]}, trying with team {team_ids[1]}")
                result = await execute_tool(
                    self.api_client,
                    "fixtures_search",
                    {"team_id": team_ids[1], "next": 1},
                )
                if isinstance(result, dict):
                    fixtures = result.get("fixtures") or []
                    logger.info(f"fixtures_search returned {len(fixtures)} fixtures for team {team_ids[1]}")
                    for fx in fixtures:
                        teams_block = fx.get("teams") or {}
                        home_id = (teams_block.get("home") or {}).get("id")
                        away_id = (teams_block.get("away") or {}).get("id")
                        logger.info(f"Checking fixture: home={home_id}, away={away_id}")
                        if (home_id in team_ids and away_id in team_ids):
                            fixture = fx.get("fixture") or {}
                            league = fx.get("league") or {}
                            fixture_id = fixture.get("id") or fixture_id
                            league_id = league_id or league.get("id")
                            season = season or league.get("season")
                            logger.info(f"MATCH FOUND on second attempt! fixture_id={fixture_id}, league_id={league_id}, season={season}")
                            break
                    if not (fixture_id):
                        logger.warning(f"Match still not found after trying both teams")

            tool_results.append(
                ToolCallResult(
                    name="fixtures_search",
                    arguments={"team_id": team_ids[0], "next": 1},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
            available_tools.add("fixtures_search")

        # Si on a un fixture_id, on peut continuer même sans teams (on les récupérera du fixture)
        if len(team_ids) < 2 and not fixture_id:
            logger.warning(f"Force critical tools: not enough teams found ({len(team_ids)}) and no fixture_id; skipping force execution.")
            return tool_results

        # Si on a le fixture_id mais pas les teams, récupérons-les depuis fixtures_search
        if fixture_id and len(team_ids) < 2:
            logger.info(f"Fetching teams from fixture {fixture_id}")
            result = await execute_tool(
                self.api_client,
                "fixtures_search",
                {"fixture_id": fixture_id},
            )
            if isinstance(result, dict):
                fixtures = result.get("fixtures") or []
                if fixtures:
                    fx = fixtures[0]
                    teams_block = fx.get("teams") or {}
                    home_team = teams_block.get("home") or {}
                    away_team = teams_block.get("away") or {}
                    for tid in [home_team.get("id"), away_team.get("id")]:
                        if tid and tid not in team_ids:
                            team_ids.append(tid)
                    # Mettre à jour league et season si pas déjà définis
                    if not league_id:
                        league = fx.get("league") or {}
                        league_id = league.get("id")
                    if not season:
                        league = fx.get("league") or {}
                        season = league.get("season")
                    logger.info(f"Retrieved {len(team_ids)} teams from fixture: {team_ids}")

            # Si toujours pas assez de teams, skip
            if len(team_ids) < 2:
                logger.warning(f"Force critical tools: could not find teams even with fixture_id {fixture_id}")
                return tool_results

        # Fallbacks
        now = datetime.utcnow()
        if not season:
            season = now.year if now.month >= 8 else now.year - 1
            logger.info(f"Season not found, using fallback: {season}")
        if not league_id and fixture_id:
            # try to recover from intent default league mapping (Premier League 39) as last resort
            league_id = intent.entities.get("league_id") or 39
            logger.info(f"League ID not found, using fallback: {league_id}")

        logger.info("-" * 80)
        logger.info("STARTING FORCED TOOL EXECUTIONS")
        logger.info(f"Final parameters: fixture_id={fixture_id}, league_id={league_id}, season={season}, team_ids={team_ids[:2]}")

        # Force executions using execute_tool
        # 1. team_last_fixtures for both teams if missing
        logger.info("[1/7] Executing team_last_fixtures for both teams")
        for tid in team_ids[:2]:
            if tid in team_last_fixtures_done:
                logger.info(f"  -> team_last_fixtures already done for team {tid}, skipping")
                continue
            logger.info(f"  -> Force-executing team_last_fixtures for team {tid}")
            result = await execute_tool(self.api_client, "team_last_fixtures", {"team_id": tid, "count": 5})
            fixtures_count = len(result.get("fixtures", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {fixtures_count} last fixtures for team {tid}")
            tool_results.append(
                ToolCallResult(
                    name="team_last_fixtures",
                    arguments={"team_id": tid, "count": 5},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 2. standings
        logger.info("[2/7] Executing standings")
        if "standings" not in available_tools and league_id and season:
            logger.info(f"  -> Force-executing standings for league {league_id}, season {season}")
            result = await execute_tool(
                self.api_client,
                "standings",
                {"league_id": league_id, "season": season},
            )
            standings_count = len(result.get("standings", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {standings_count} standings entries")
            tool_results.append(
                ToolCallResult(
                    name="standings",
                    arguments={"league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping standings (already called or missing league_id/season)")

        # 3. head_to_head
        logger.info("[3/7] Executing head_to_head")
        if "head_to_head" not in available_tools:
            logger.info(f"  -> Force-executing head_to_head for teams {team_ids[0]} vs {team_ids[1]}")
            result = await execute_tool(
                self.api_client,
                "head_to_head",
                {"team1_id": team_ids[0], "team2_id": team_ids[1]},
            )
            h2h_count = len(result.get("fixtures", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {h2h_count} head-to-head fixtures")
            tool_results.append(
                ToolCallResult(
                    name="head_to_head",
                    arguments={"team1_id": team_ids[0], "team2_id": team_ids[1]},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping head_to_head (already called)")

        # 4. team_statistics for both teams (avec fallback si pas de données pour la ligue actuelle)
        logger.info("[4/7] Executing team_statistics for both teams")
        for tid in team_ids[:2]:
            if tid in team_statistics_done:
                logger.info(f"  -> team_statistics already done for team {tid}, skipping")
                continue

            logger.info(f"  -> Force-executing team_statistics for team {tid}")

            # Essayer d'abord avec la ligue et saison actuelles
            if league_id and season:
                result = await execute_tool(
                    self.api_client,
                    "team_statistics",
                    {"team_id": tid, "league_id": league_id, "season": season},
                )

                # Si pas de données (1ère journée par exemple), chercher dans les derniers matchs toutes ligues
                stats_data = result.get("statistics") if isinstance(result, dict) else None
                if not stats_data or (isinstance(stats_data, dict) and not stats_data.get("fixtures")):
                    logger.info(f"  -> No stats for team {tid} in league {league_id} (probably first matchday)")
                    logger.info(f"  -> Stats will be inferred from recent matches across all leagues")
                    # Les stats seront inférées des derniers matchs déjà récupérés
                    result = {"statistics": None, "note": "No data for this league yet, check recent matches"}
                else:
                    logger.info(f"  -> Retrieved team_statistics for team {tid}")
            else:
                logger.info(f"  -> Missing league_id or season for team_statistics")
                result = {"statistics": None, "note": "Missing league_id or season"}

            tool_results.append(
                ToolCallResult(
                    name="team_statistics",
                    arguments={"team_id": tid, "league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 5. fixture_lineups - Compositions d'équipe (si fixture_id disponible)
        logger.info("[5/7] Executing fixture_lineups")
        if "fixture_lineups" not in available_tools and fixture_id:
            logger.info(f"  -> Force-executing fixture_lineups for fixture {fixture_id}")
            result = await execute_tool(
                self.api_client,
                "fixture_lineups",
                {"fixture_id": fixture_id},
            )
            # Si pas de lineup disponible (match pas encore joué), essayer de récupérer les compos des derniers matchs
            lineups_data = result.get("lineups") if isinstance(result, dict) else None
            if not lineups_data or len(lineups_data) == 0:
                logger.info(f"  -> No lineups available for fixture {fixture_id} (match not started yet)")
                logger.info(f"  -> FALLBACK: Fetching lineups from recent matches for both teams")
                # Récupérer les lineups des derniers matchs pour chaque équipe
                for tid in team_ids[:2]:
                    logger.info(f"  -> Fetching recent lineup for team {tid}")
                    last_fixtures_result = next(
                        (tr.output for tr in tool_results if tr.name == "team_last_fixtures" and tr.arguments.get("team_id") == tid),
                        None
                    )
                    if last_fixtures_result and isinstance(last_fixtures_result, dict):
                        fixtures_list = last_fixtures_result.get("fixtures", [])
                        if fixtures_list and len(fixtures_list) > 0:
                            # Prendre le lineup du dernier match
                            last_fixture = fixtures_list[0]
                            last_fixture_id = last_fixture.get("fixture", {}).get("id")
                            if last_fixture_id:
                                logger.info(f"  -> Fetching lineup from last match {last_fixture_id} for team {tid}")
                                lineup_result = await execute_tool(
                                    self.api_client,
                                    "fixture_lineups",
                                    {"fixture_id": last_fixture_id, "team_id": tid},
                                )
                                lineups_retrieved = len(lineup_result.get("lineups", [])) if isinstance(lineup_result, dict) else 0
                                logger.info(f"  -> Retrieved {lineups_retrieved} lineups from last match for team {tid}")
                                tool_results.append(
                                    ToolCallResult(
                                        name="fixture_lineups",
                                        arguments={"fixture_id": last_fixture_id, "team_id": tid},
                                        output=lineup_result,
                                        error=lineup_result.get("error") if isinstance(lineup_result, dict) else None,
                                    )
                                )
                    else:
                        logger.warning(f"  -> No last fixtures found for team {tid}, cannot get fallback lineup")
            else:
                logger.info(f"  -> Retrieved {len(lineups_data)} lineups for fixture {fixture_id}")
                tool_results.append(
                    ToolCallResult(
                        name="fixture_lineups",
                        arguments={"fixture_id": fixture_id},
                        output=result,
                        error=result.get("error") if isinstance(result, dict) else None,
                    )
                )
        else:
            logger.info(f"  -> Skipping fixture_lineups (already called or missing fixture_id)")

        # 6. injuries - Joueurs blessés/absents pour les deux équipes
        logger.info("[6/7] Executing injuries")
        if "injuries" not in available_tools and fixture_id:
            logger.info(f"  -> Force-executing injuries for fixture {fixture_id}")
            result = await execute_tool(
                self.api_client,
                "injuries",
                {"fixture_id": fixture_id},
            )
            injuries_count = len(result.get("injuries", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {injuries_count} injuries")
            tool_results.append(
                ToolCallResult(
                    name="injuries",
                    arguments={"fixture_id": fixture_id},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping injuries (already called or missing fixture_id)")

        # 7. fixture_rounds - Journée actuelle de la ligue
        logger.info("[7/15] Executing fixture_rounds")
        if "fixture_rounds" not in available_tools and league_id and season:
            logger.info(f"  -> Force-executing fixture_rounds (current) for league {league_id}, season {season}")
            result = await execute_tool(
                self.api_client,
                "fixture_rounds",
                {"league_id": league_id, "season": season, "current": True},
            )
            rounds_data = result.get("rounds") if isinstance(result, dict) else None
            if rounds_data:
                logger.info(f"  -> Retrieved current round: {rounds_data}")
            else:
                logger.info(f"  -> No rounds data available")
            tool_results.append(
                ToolCallResult(
                    name="fixture_rounds",
                    arguments={"league_id": league_id, "season": season, "current": True},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping fixture_rounds (already called or missing league_id/season)")

        # 8. league_type - Détecter si c'est une Coupe ou un Championnat
        logger.info("[8/15] Executing league_type")
        if "league_type" not in available_tools and league_id:
            logger.info(f"  -> Force-executing league_type for league {league_id}")
            result = await execute_tool(
                self.api_client,
                "league_type",
                {"league_id": league_id, "season": season},
            )
            league_type = result.get("type") if isinstance(result, dict) else "Unknown"
            logger.info(f"  -> League type: {league_type}")
            tool_results.append(
                ToolCallResult(
                    name="league_type",
                    arguments={"league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping league_type (already called or missing league_id)")

        # 9. team_form_stats - Statistiques de forme pour les deux équipes
        logger.info("[9/15] Executing team_form_stats for both teams")
        for tid in team_ids[:2]:
            if any(tr.name == "team_form_stats" and tr.arguments.get("team_id") == tid for tr in tool_results):
                logger.info(f"  -> team_form_stats already done for team {tid}, skipping")
                continue
            logger.info(f"  -> Force-executing team_form_stats for team {tid}")
            result = await execute_tool(
                self.api_client,
                "team_form_stats",
                {"team_id": tid, "last_n": 10},
            )
            form = result.get("form", "") if isinstance(result, dict) else ""
            logger.info(f"  -> Team {tid} form: {form}")
            tool_results.append(
                ToolCallResult(
                    name="team_form_stats",
                    arguments={"team_id": tid, "last_n": 10},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )

        # 10. top_scorers - Meilleurs buteurs de la ligue
        logger.info("[10/15] Executing top_scorers")
        if "top_scorers" not in available_tools and league_id and season:
            logger.info(f"  -> Force-executing top_scorers for league {league_id}, season {season}")
            result = await execute_tool(
                self.api_client,
                "top_scorers",
                {"league_id": league_id, "season": season},
            )
            scorers_count = len(result.get("top_scorers", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {scorers_count} top scorers")
            tool_results.append(
                ToolCallResult(
                    name="top_scorers",
                    arguments={"league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping top_scorers (already called or missing league_id/season)")

        # 11. top_assists - Meilleurs passeurs de la ligue
        logger.info("[11/15] Executing top_assists")
        if "top_assists" not in available_tools and league_id and season:
            logger.info(f"  -> Force-executing top_assists for league {league_id}, season {season}")
            result = await execute_tool(
                self.api_client,
                "top_assists",
                {"league_id": league_id, "season": season},
            )
            assists_count = len(result.get("top_assists", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {assists_count} top assists")
            tool_results.append(
                ToolCallResult(
                    name="top_assists",
                    arguments={"league_id": league_id, "season": season},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping top_assists (already called or missing league_id/season)")

        # 12. fixture_players - Stats des joueurs dans les derniers matchs
        logger.info("[12/15] Executing fixture_players for recent matches")
        for tid in team_ids[:2]:
            # Récupérer les fixture_ids des derniers matchs de cette équipe
            last_fixtures_result = next(
                (tr.output for tr in tool_results if tr.name == "team_last_fixtures" and tr.arguments.get("team_id") == tid),
                None
            )
            if last_fixtures_result and isinstance(last_fixtures_result, dict):
                fixtures_list = last_fixtures_result.get("fixtures", [])[:2]  # Prendre les 2 derniers matchs
                for fixture in fixtures_list:
                    fixture_id_for_players = fixture.get("fixture_id")
                    if fixture_id_for_players:
                        # Vérifier si on a déjà récupéré les stats de ce match
                        if any(tr.name == "fixture_players" and tr.arguments.get("fixture_id") == fixture_id_for_players for tr in tool_results):
                            continue
                        logger.info(f"  -> Force-executing fixture_players for fixture {fixture_id_for_players}, team {tid}")
                        result = await execute_tool(
                            self.api_client,
                            "fixture_players",
                            {"fixture_id": fixture_id_for_players, "team_id": tid},
                        )
                        players_count = len(result.get("players", [])) if isinstance(result, dict) else 0
                        logger.info(f"  -> Retrieved stats for {players_count} players")
                        tool_results.append(
                            ToolCallResult(
                                name="fixture_players",
                                arguments={"fixture_id": fixture_id_for_players, "team_id": tid},
                                output=result,
                                error=result.get("error") if isinstance(result, dict) else None,
                            )
                        )

        # 13. fixture_statistics - Stats détaillées du match analysé (pour les DEUX équipes)
        logger.info("[13/15] Executing fixture_statistics for the match being analyzed")
        # Vérifier si fixture_statistics a déjà été appelé SANS team_id (pour avoir les 2 équipes)
        has_full_stats = any(
            tr.name == "fixture_statistics"
            and tr.arguments.get("fixture_id") == fixture_id
            and not tr.arguments.get("team_id")
            for tr in tool_results
        )

        if not has_full_stats and fixture_id:
            logger.info(f"  -> Force-executing fixture_statistics for fixture {fixture_id} (both teams)")
            result = await execute_tool(
                self.api_client,
                "fixture_statistics",
                {"fixture_id": fixture_id},  # SANS team_id pour avoir les 2 équipes
            )
            stats_count = len(result.get("statistics", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved statistics for {stats_count} teams")
            tool_results.append(
                ToolCallResult(
                    name="fixture_statistics",
                    arguments={"fixture_id": fixture_id},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            reason = "missing fixture_id" if not fixture_id else "already called for both teams"
            logger.info(f"  -> Skipping fixture_statistics ({reason})")

        # 14. fixture_events - Événements du match analysé (buts, cartons, substitutions)
        logger.info("[14/15] Executing fixture_events for the match being analyzed")
        if "fixture_events" not in available_tools and fixture_id:
            logger.info(f"  -> Force-executing fixture_events for fixture {fixture_id}")
            result = await execute_tool(
                self.api_client,
                "fixture_events",
                {"fixture_id": fixture_id},
            )
            events_count = len(result.get("events", [])) if isinstance(result, dict) else 0
            logger.info(f"  -> Retrieved {events_count} events (goals, cards, substitutions)")
            tool_results.append(
                ToolCallResult(
                    name="fixture_events",
                    arguments={"fixture_id": fixture_id},
                    output=result,
                    error=result.get("error") if isinstance(result, dict) else None,
                )
            )
        else:
            logger.info(f"  -> Skipping fixture_events (already called or missing fixture_id)")

        # 15. fixture_players - Stats joueurs pour le match analysé
        logger.info("[15/15] Executing fixture_players for the match being analyzed")
        if fixture_id:
            # Vérifier si on a déjà récupéré les stats de ce match
            if not any(tr.name == "fixture_players" and tr.arguments.get("fixture_id") == fixture_id and not tr.arguments.get("team_id") for tr in tool_results):
                logger.info(f"  -> Force-executing fixture_players for fixture {fixture_id}")
                result = await execute_tool(
                    self.api_client,
                    "fixture_players",
                    {"fixture_id": fixture_id},
                )
                players_data = result.get("players", []) if isinstance(result, dict) else []
                logger.info(f"  -> Retrieved stats for {len(players_data)} teams")
                tool_results.append(
                    ToolCallResult(
                        name="fixture_players",
                        arguments={"fixture_id": fixture_id},
                        output=result,
                        error=result.get("error") if isinstance(result, dict) else None,
                    )
                )
            else:
                logger.info(f"  -> fixture_players already called for fixture {fixture_id}")
        else:
            logger.info(f"  -> Skipping fixture_players for analyzed match (missing fixture_id)")

        logger.info("="*80)
        logger.info("FIN FORCE CRITICAL TOOLS FOR MATCH ANALYSIS")
        logger.info(f"Total tools executed: {len(tool_results)}")
        logger.info("="*80)

        return tool_results

    async def _execute_tool_call(
        self,
        tool_call,
        default_season: Optional[int],
        semaphore: Optional[asyncio.Semaphore],
    ) -> Tuple[ToolCallResult, Dict[str, Any]]:
        try:
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {}

            if default_season and tool_call.function.name in SEASONAL_TOOLS:
                if arguments.get("season") != default_season:
                    arguments["season"] = default_season

            logger.info("Executing tool %s with args %s", tool_call.function.name, arguments)

            async def _run():
                if tool_call.function.name == "analyze_match" and self.context_agent:
                    fixture_id = arguments.get("fixture_id")
                    bet_type = arguments.get("bet_type")

                    if not fixture_id:
                        return {"error": "fixture_id is required for analyze_match"}

                    try:
                        context_data = await self.context_agent.get_match_context(fixture_id)
                        context = context_data["context"]

                        if bet_type:
                            analysis = context.analyses.get(bet_type)
                            if analysis:
                                return {
                                    "fixture_id": fixture_id,
                                    "match": f"{context.home_team} vs {context.away_team}",
                                    "bet_type": bet_type,
                                    "indicators": analysis.indicators,
                                    "coverage_complete": analysis.coverage_complete,
                                    "source": context_data["source"],
                                    "api_calls": context_data["api_calls"],
                                }
                            return {"error": f"Bet type '{bet_type}' not found"}

                        return {
                            "fixture_id": fixture_id,
                            "match": f"{context.home_team} vs {context.away_team}",
                            "league": context.league,
                            "date": str(context.date) if context.date else None,
                            "status": context.status,
                            "available_analyses": list(context.analyses.keys()),
                            "source": context_data["source"],
                            "api_calls": context_data["api_calls"],
                        }
                    except Exception as exc:
                        return {"error": f"Failed to analyze match: {str(exc)}"}

                return await execute_tool(self.api_client, tool_call.function.name, arguments)

            if semaphore:
                async with semaphore:
                    result = await _run()
            else:
                result = await _run()

            error = result.get("error") if isinstance(result, dict) else None
            tool_result = ToolCallResult(
                name=tool_call.function.name,
                arguments=arguments,
                output=result,
                error=error,
            )
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False),
            }
            return tool_result, tool_message
        except Exception as exc:
            logger.error("Tool execution failed: %s", exc, exc_info=True)
            error_payload = {"error": str(exc)}
            tool_result = ToolCallResult(
                name=getattr(tool_call.function, "name", "unknown"),
                arguments={},
                output=error_payload,
                error=str(exc),
            )
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(error_payload, ensure_ascii=False),
            }
            return tool_result, tool_message

    async def _force_player_stats_tools(
        self,
        context: Optional[Dict[str, Any]],
        tool_results: List[ToolCallResult],
    ) -> List[ToolCallResult]:
        """
        Force player stats tools when player context is provided.
        - If match_id + player_id: fetch fixture_players for that specific match
        - If team_id + player_id (no match): fetch player_statistics for the season
        """
        if not context or "player_id" not in context:
            return tool_results

        player_id = context.get("player_id")
        match_id = context.get("match_id") or context.get("fixture_id")
        team_id = context.get("team_id")
        season = context.get("season") or _default_season_for_request("", context)

        logger.info("="*80)
        logger.info("DEBUT FORCE PLAYER STATS TOOLS")
        logger.info(f"Player ID: {player_id}")
        logger.info(f"Match ID: {match_id}")
        logger.info(f"Team ID: {team_id}")
        logger.info(f"Season: {season}")

        # Case 1: Match + Player = player stats in that specific match
        if match_id and player_id:
            logger.info(f"Context: MATCH mode - fetching player stats for match {match_id}")

            # Check if fixture_players already called for this match
            has_fixture_players = any(
                tr.name == "fixture_players"
                and tr.arguments.get("fixture_id") == match_id
                for tr in tool_results
            )

            if not has_fixture_players:
                logger.info(f"  -> Force-executing fixture_players for match {match_id}")
                result = await execute_tool(
                    self.api_client,
                    "fixture_players",
                    {"fixture_id": match_id},
                )
                tool_results.append(
                    ToolCallResult(
                        name="fixture_players",
                        arguments={"fixture_id": match_id},
                        output=result,
                        error=result.get("error") if isinstance(result, dict) else None,
                    )
                )
                logger.info(f"  -> Retrieved player stats for match {match_id}")
            else:
                logger.info(f"  -> fixture_players already called for match {match_id}")

        # Case 2: Team + Player (no match) = player season stats
        elif team_id and player_id and not match_id:
            logger.info(f"Context: TEAM mode - fetching player season stats for player {player_id}")

            # Check if player_statistics already called for this player
            has_player_stats = any(
                tr.name == "player_statistics"
                and tr.arguments.get("player_id") == player_id
                and tr.arguments.get("season") == season
                for tr in tool_results
            )

            if not has_player_stats:
                logger.info(f"  -> Force-executing player_statistics for player {player_id}, season {season}")
                result = await execute_tool(
                    self.api_client,
                    "player_statistics",
                    {"player_id": player_id, "season": season},
                )
                tool_results.append(
                    ToolCallResult(
                        name="player_statistics",
                        arguments={"player_id": player_id, "season": season},
                        output=result,
                        error=result.get("error") if isinstance(result, dict) else None,
                    )
                )
                logger.info(f"  -> Retrieved season stats for player {player_id}")
            else:
                logger.info(f"  -> player_statistics already called for player {player_id}")

        logger.info("FIN FORCE PLAYER STATS TOOLS")
        logger.info("="*80)

        return tool_results

    async def run(
        self,
        user_message: str,
        intent: IntentResult,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[ToolCallResult], str]:
        league_mapping = (
            "Mapping ligues vers IDs: "
            "Ligue 1=61; Premier League=39; La Liga=140; Bundesliga=78; Serie A=135; "
            "Ligue des Champions=2; Europa League=3."
        )
        intent_guidance = {
            "classement_ligue": "Utilise le tool standings avec league_id et season (convertis le nom de ligue via le mapping).",
            "live_scores": "Si aucune ligue precisee, utilise live_fixtures; sinon fixtures_search live='all' + league_id.",
            "prochain_match_equipe": "Utilise search_team puis team_next_fixtures (count=1 par defaut).",
            "stats_live": (
                "CRITIQUE: 1) search_team equipe1, 2) search_team equipe2, "
                "3) fixtures_search pour obtenir fixture_id, "
                "4) OBLIGATOIREMENT appeler fixture_statistics avec le fixture_id. "
                "NE PAS utiliser head_to_head ou autres endpoints - fixture_statistics contient toutes les stats (possession, tirs, corners, passes)."
            ),
            "stats_final": (
                "CRITIQUE: 1) search_team equipe1, 2) search_team equipe2, "
                "3) fixtures_search pour obtenir fixture_id, "
                "4) OBLIGATOIREMENT appeler fixture_statistics avec le fixture_id. "
                "NE PAS utiliser head_to_head ou autres endpoints - fixture_statistics contient toutes les stats (possession, tirs, corners, passes)."
            ),
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

        normalized_intent = "analyse_rencontre" if intent.intent == "match_analysis" else intent.intent
        default_season = _default_season_for_request(user_message, context)

        messages = [
            {"role": "system", "content": TOOL_SYSTEM_PROMPT},
            {
                "role": "system",
                "content": f"Intent cible: {normalized_intent}. Entites: {intent.entities}. "
                "Si needs_data est False, reponds directement par une courte note sans tool.",
            },
            {
                "role": "system",
                "content": (
                    f"Context payload: {json.dumps(context, ensure_ascii=True)}"
                    if context else "Context payload: none"
                ),
            },
            {"role": "system", "content": league_mapping},
            {
                "role": "system",
                "content": intent_guidance.get(
                    normalized_intent,
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

                if settings.ENABLE_PARALLEL_API_CALLS and len(msg.tool_calls) > 1:
                    semaphore = asyncio.Semaphore(max(1, settings.MAX_PARALLEL_TOOL_CALLS))
                    tasks = [
                        self._execute_tool_call(tool_call, default_season, semaphore)
                        for tool_call in msg.tool_calls
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for idx, result in enumerate(results):
                        if isinstance(result, Exception):
                            error_payload = {"error": str(result)}
                            tool_results.append(
                                ToolCallResult(
                                    name=msg.tool_calls[idx].function.name,
                                    arguments={},
                                    output=error_payload,
                                    error=str(result),
                                )
                            )
                            conversation.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": msg.tool_calls[idx].id,
                                    "content": json.dumps(error_payload, ensure_ascii=False),
                                }
                            )
                            continue
                        tool_result, tool_message = result
                        tool_results.append(tool_result)
                        conversation.append(tool_message)
                else:
                    for tool_call in msg.tool_calls:
                        tool_result, tool_message = await self._execute_tool_call(
                            tool_call,
                            default_season,
                            None,
                        )
                        tool_results.append(tool_result)
                        conversation.append(tool_message)
                continue

            assistant_notes = msg.content or ""
            break

        # After LLM loop, force missing critical tools for match analysis if needed
        tool_results = await self._force_critical_tools_for_match_analysis(intent, tool_results)

        # Force player stats tools if player context is provided
        tool_results = await self._force_player_stats_tools(context, tool_results)

        return tool_results, assistant_notes
