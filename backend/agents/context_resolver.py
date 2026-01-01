import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from backend.api.football_api import FootballAPIClient
from backend.agents.types import IntentResult

logger = logging.getLogger(__name__)

YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


@dataclass
class ContextResolution:
    context: Optional[Dict[str, Any]] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    clarification_question: Optional[str] = None


class ContextResolver:
    """
    Resolve match/team/player/league context from user intent entities.
    Builds minimal context needed for API calls and asks for clarification when ambiguous.
    """

    def __init__(self, api_client: FootballAPIClient):
        self.api_client = api_client

    async def resolve(
        self,
        user_message: str,
        intent: IntentResult,
        language: str = "fr",
        existing_context: Optional[Dict[str, Any]] = None,
    ) -> ContextResolution:
        entities = intent.entities or {}

        if existing_context and not self._has_explicit_entities(entities):
            if self._context_satisfies_intent(existing_context, intent.intent):
                return ContextResolution(
                    context=existing_context,
                    entities=self._entities_from_context(existing_context),
                )

        context_type = self._infer_context_type(entities, intent.intent)
        if not context_type:
            return ContextResolution(context=existing_context)

        if context_type == "match":
            return await self._resolve_match_context(
                user_message, entities, intent.intent, language, existing_context
            )
        if context_type in {"team", "league_team"}:
            return await self._resolve_team_context(
                user_message, entities, language, existing_context
            )
        if context_type == "league":
            return await self._resolve_league_context(
                user_message, entities, language, existing_context
            )
        if context_type == "player":
            return await self._resolve_player_context(
                user_message, entities, language, existing_context
            )

        return ContextResolution(context=existing_context)

    def _infer_context_type(self, entities: Dict[str, Any], intent_name: str) -> Optional[str]:
        if entities.get("player") or entities.get("player_id"):
            return "player"
        if entities.get("fixture_id") or entities.get("match_id"):
            return "match"
        if entities.get("home_team") or entities.get("away_team"):
            return "match"
        if entities.get("team") or entities.get("team_id"):
            if entities.get("league") or entities.get("league_id"):
                return "league_team"
            return "team"
        if entities.get("league") or entities.get("league_id"):
            return "league"

        if intent_name in MATCH_INTENTS:
            return "match"
        if intent_name in PLAYER_INTENTS:
            return "player"
        if intent_name in TEAM_INTENTS:
            return "team"
        if intent_name in LEAGUE_INTENTS:
            return "league"

        return None

    def _has_explicit_entities(self, entities: Dict[str, Any]) -> bool:
        keys = (
            "player",
            "player_id",
            "team",
            "team_id",
            "home_team",
            "away_team",
            "league",
            "league_id",
            "fixture_id",
            "match_id",
        )
        return any(entities.get(key) for key in keys)

    def _entities_from_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        mapping: Dict[str, Any] = {}
        for key in (
            "fixture_id",
            "league_id",
            "team_id",
            "player_id",
            "season",
            "home_team_id",
            "away_team_id",
        ):
            if context.get(key) is not None:
                mapping[key] = context[key]
        return mapping

    def _context_satisfies_intent(self, context: Dict[str, Any], intent_name: str) -> bool:
        context_type = context.get("context_type")
        if intent_name in PLAYER_INTENTS:
            return bool(context.get("player_id"))
        if intent_name in MATCH_INTENTS:
            return bool(context.get("fixture_id")) or (
                context.get("home_team_id") and context.get("away_team_id")
            )
        if intent_name in TEAM_INTENTS:
            return bool(context.get("team_id"))
        if intent_name in LEAGUE_INTENTS:
            return bool(context.get("league_id"))

        if context_type == "player":
            return bool(context.get("player_id"))
        if context_type == "match":
            return bool(context.get("fixture_id")) or (
                context.get("home_team_id") and context.get("away_team_id")
            )
        if context_type in {"team", "league_team"}:
            return bool(context.get("team_id"))
        if context_type == "league":
            return bool(context.get("league_id"))
        return False

    async def _resolve_league_context(
        self,
        user_message: str,
        entities: Dict[str, Any],
        language: str,
        context_hint: Optional[Dict[str, Any]],
    ) -> ContextResolution:
        league_id = self._coerce_int(
            entities.get("league_id") or (context_hint or {}).get("league_id")
        )
        league_name = entities.get("league") or (context_hint or {}).get("league_name")
        season = self._resolve_season(entities, user_message)

        if league_id:
            leagues = await self.api_client.get_leagues(league_id=league_id, season=season)
            if not leagues:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "league_not_found", name=str(league_id)
                    )
                )
            league_entry = leagues[0]
        elif league_name:
            league_entry, options = await self._resolve_league_by_name(league_name, season)
            if not league_entry:
                if not options:
                    return ContextResolution(
                        clarification_question=self._question(
                            language, "league_not_found", name=league_name
                        )
                    )
                return ContextResolution(
                    clarification_question=self._question(
                        language,
                        "league_ambiguous",
                        name=league_name,
                        options=self._format_league_options(options),
                    )
                )
        else:
            return ContextResolution(
                clarification_question=self._question(language, "league_missing")
            )

        league_data = league_entry.get("league", {}) or {}
        country_data = league_entry.get("country", {}) or {}
        season = season or self._season_from_league_entry(league_entry)

        context = {
            "context_type": "league",
            "league_id": league_data.get("id"),
            "league_name": league_data.get("name"),
            "competition_name": league_data.get("name"),
            "country": country_data.get("name"),
            "season": season,
        }
        return ContextResolution(context=context, entities=self._entities_from_context(context))

    async def _resolve_team_context(
        self,
        user_message: str,
        entities: Dict[str, Any],
        language: str,
        context_hint: Optional[Dict[str, Any]],
    ) -> ContextResolution:
        team_id = self._coerce_int(entities.get("team_id") or (context_hint or {}).get("team_id"))
        team_name = entities.get("team") or (context_hint or {}).get("team_name")
        league_id = self._coerce_int(entities.get("league_id") or (context_hint or {}).get("league_id"))
        league_name = entities.get("league") or (context_hint or {}).get("league_name")
        season = self._resolve_season(entities, user_message)

        if team_id:
            teams = await self.api_client.get_teams(team_id=team_id)
            if not teams:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "team_not_found", name=str(team_id)
                    )
                )
            team_entry = teams[0]
        elif team_name:
            team_entry, options = await self._resolve_team_by_name(team_name, league_id, season)
            if not team_entry:
                if not options:
                    return ContextResolution(
                        clarification_question=self._question(
                            language, "team_not_found", name=team_name
                        )
                    )
                return ContextResolution(
                    clarification_question=self._question(
                        language,
                        "team_ambiguous",
                        name=team_name,
                        options=self._format_team_options(options),
                    )
                )
        else:
            return ContextResolution(
                clarification_question=self._question(language, "team_missing")
            )

        if not league_id and league_name:
            league_entry, options = await self._resolve_league_by_name(league_name, season)
            if not league_entry and options:
                return ContextResolution(
                    clarification_question=self._question(
                        language,
                        "league_ambiguous",
                        name=league_name,
                        options=self._format_league_options(options),
                    )
                )
            if league_entry:
                league_id = self._coerce_int(league_entry.get("league", {}).get("id"))
                league_name = league_entry.get("league", {}).get("name")
                season = season or self._season_from_league_entry(league_entry)

        team_data = team_entry.get("team", {}) or team_entry
        context = {
            "context_type": "league_team" if league_id else "team",
            "team_id": team_data.get("id"),
            "team_name": team_data.get("name"),
            "team_code": team_data.get("code"),
            "country": team_data.get("country"),
            "founded": team_data.get("founded"),
            "logo": team_data.get("logo"),
            "league_id": league_id,
            "league_name": league_name,
            "season": season,
        }
        return ContextResolution(context=context, entities=self._entities_from_context(context))

    async def _resolve_player_context(
        self,
        user_message: str,
        entities: Dict[str, Any],
        language: str,
        context_hint: Optional[Dict[str, Any]],
    ) -> ContextResolution:
        player_id = self._coerce_int(
            entities.get("player_id") or (context_hint or {}).get("player_id")
        )
        player_name = entities.get("player") or (context_hint or {}).get("player_name")
        team_name = entities.get("team") or (context_hint or {}).get("team_name")
        team_id = self._coerce_int(entities.get("team_id") or (context_hint or {}).get("team_id"))
        league_id = self._coerce_int(entities.get("league_id") or (context_hint or {}).get("league_id"))
        season = self._resolve_season(entities, user_message)

        player_entry: Optional[Dict[str, Any]] = None
        options: List[Dict[str, Any]] = []

        if player_id:
            data = await self.api_client.get_players(player_id=player_id, season=season)
            options = data.get("response", []) if isinstance(data, dict) else []
            player_entry = options[0] if options else None
        elif player_name:
            # API requires league_id OR team_id when using search
            # If we don't have either, first search profiles to get player_id
            if not league_id and not team_id:
                profiles = await self.api_client.get_player_profiles(search=player_name)
                if profiles:
                    # Pick the best match
                    profile = self._pick_exact_match(
                        profiles,
                        player_name,
                        lambda p: (p.get("player", {}) or {}).get("name")
                    ) or profiles[0]

                    found_player_id = self._coerce_int(
                        (profile.get("player", {}) or {}).get("id")
                    )
                    if found_player_id:
                        # Now search with player_id instead
                        data = await self.api_client.get_players(
                            player_id=found_player_id,
                            season=season
                        )
                        options = data.get("response", []) if isinstance(data, dict) else []
                        player_entry = options[0] if options else None
                    else:
                        options = []
                        player_entry = None
                else:
                    options = []
                    player_entry = None
            else:
                # We have league_id or team_id, so we can search normally
                data = await self.api_client.get_players(
                    search=player_name,
                    season=season,
                    team_id=team_id,
                    league_id=league_id
                )
                options = data.get("response", []) if isinstance(data, dict) else []
                if team_id:
                    options = [p for p in options if self._player_has_team_id(p, team_id)]
                elif team_name:
                    options = [p for p in options if self._player_has_team_name(p, team_name)]

                player_entry = self._pick_player_match(options, player_name)
        else:
            return ContextResolution(
                clarification_question=self._question(language, "player_missing")
            )

        if not player_entry:
            if not options:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "player_not_found", name=player_name or str(player_id)
                    )
                )
            return ContextResolution(
                clarification_question=self._question(
                    language,
                    "player_ambiguous",
                    name=player_name or "ce joueur",
                    options=self._format_player_options(options),
                )
            )

        player_data = player_entry.get("player", {}) or {}
        stats_block = (player_entry.get("statistics") or [{}])[0]
        games = stats_block.get("games", {}) or {}
        team_block = stats_block.get("team", {}) or {}

        context = {
            "context_type": "player",
            "player_id": player_data.get("id"),
            "player_name": player_data.get("name"),
            "firstname": player_data.get("firstname"),
            "lastname": player_data.get("lastname"),
            "age": player_data.get("age"),
            "nationality": player_data.get("nationality"),
            "position": player_data.get("position") or games.get("position"),
            "current_team": team_block.get("name"),
            "current_team_id": team_block.get("id"),
            "team_id": team_id or team_block.get("id"),
            "league_id": league_id,
            "season": season,
        }
        if entities.get("fixture_id") or entities.get("match_id"):
            context["fixture_id"] = self._coerce_int(entities.get("fixture_id") or entities.get("match_id"))
        return ContextResolution(context=context, entities=self._entities_from_context(context))

    async def _resolve_match_context(
        self,
        user_message: str,
        entities: Dict[str, Any],
        intent_name: str,
        language: str,
        context_hint: Optional[Dict[str, Any]],
    ) -> ContextResolution:
        fixture_id = self._coerce_int(
            entities.get("fixture_id") or entities.get("match_id") or (context_hint or {}).get("fixture_id")
        )
        league_id = self._coerce_int(entities.get("league_id") or (context_hint or {}).get("league_id"))
        league_name = entities.get("league") or (context_hint or {}).get("league_name")
        season = self._resolve_season(entities, user_message)
        date_str = self._normalize_date(
            entities.get("date") or entities.get("match_date") or (context_hint or {}).get("match_date")
        )

        if fixture_id:
            fixture = await self._get_fixture_by_id(fixture_id)
            if not fixture:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "fixture_not_found", name=str(fixture_id)
                    )
                )
            context = self._build_match_context_from_fixture(fixture)
            return ContextResolution(context=context, entities=self._entities_from_context(context))

        home_name = entities.get("home_team") or (context_hint or {}).get("team1_name")
        away_name = entities.get("away_team") or (context_hint or {}).get("team2_name")

        if not home_name or not away_name:
            return ContextResolution(
                clarification_question=self._question(language, "match_missing_teams")
            )

        if not league_id and league_name:
            league_entry, options = await self._resolve_league_by_name(league_name, season)
            if not league_entry and options:
                return ContextResolution(
                    clarification_question=self._question(
                        language,
                        "league_ambiguous",
                        name=league_name,
                        options=self._format_league_options(options),
                    )
                )
            if league_entry:
                league_id = self._coerce_int(league_entry.get("league", {}).get("id"))
                league_name = league_entry.get("league", {}).get("name")
                season = season or self._season_from_league_entry(league_entry)

        home_entry, home_options = await self._resolve_team_by_name(home_name, league_id, season)
        if not home_entry:
            if not home_options:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "team_not_found", name=home_name
                    )
                )
            return ContextResolution(
                clarification_question=self._question(
                    language,
                    "team_ambiguous",
                    name=home_name,
                    options=self._format_team_options(home_options),
                )
            )

        away_entry, away_options = await self._resolve_team_by_name(away_name, league_id, season)
        if not away_entry:
            if not away_options:
                return ContextResolution(
                    clarification_question=self._question(
                        language, "team_not_found", name=away_name
                    )
                )
            return ContextResolution(
                clarification_question=self._question(
                    language,
                    "team_ambiguous",
                    name=away_name,
                    options=self._format_team_options(away_options),
                )
            )

        home_team = home_entry.get("team", {}) or home_entry
        away_team = away_entry.get("team", {}) or away_entry
        home_team_id = self._coerce_int(home_team.get("id"))
        away_team_id = self._coerce_int(away_team.get("id"))

        fixture = await self._find_fixture(
            home_team_id,
            away_team_id,
            date_str,
            league_id,
            season,
            intent_name,
        )

        if not fixture:
            return ContextResolution(
                clarification_question=self._question(
                    language,
                    "fixture_not_found_teams",
                    home=home_team.get("name") or home_name,
                    away=away_team.get("name") or away_name,
                )
            )

        if isinstance(fixture, list):
            return ContextResolution(
                clarification_question=self._question(
                    language,
                    "fixture_ambiguous",
                    home=home_team.get("name") or home_name,
                    away=away_team.get("name") or away_name,
                )
            )

        context = self._build_match_context_from_fixture(fixture)
        context["home_team_id"] = home_team_id
        context["away_team_id"] = away_team_id
        if league_id and not context.get("league_id"):
            context["league_id"] = league_id
        if league_name and not context.get("league_name"):
            context["league_name"] = league_name
        if season and not context.get("season"):
            context["season"] = season
        return ContextResolution(context=context, entities=self._entities_from_context(context))

    async def _resolve_team_by_name(
        self,
        team_name: str,
        league_id: Optional[int],
        season: Optional[int],
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        # API does not allow league_id/season with search, so search first then filter
        teams = await self.api_client.get_teams(search=team_name)
        if not teams:
            return None, []

        # Filter by league_id if provided
        if league_id:
            filtered = [
                t for t in teams
                if (t.get("team", {}) or {}).get("id") and
                   any(v.get("league", {}).get("id") == league_id
                       for v in (t.get("venues", []) or []))
            ]
            # If filtering removes all results, keep original list
            if filtered:
                teams = filtered

        if len(teams) == 1:
            return teams[0], teams
        exact = self._pick_exact_match(teams, team_name, lambda t: (t.get("team", {}) or {}).get("name"))
        if exact:
            return exact, teams
        return None, teams

    async def _resolve_league_by_name(
        self,
        league_name: str,
        season: Optional[int],
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        leagues = await self.api_client.get_leagues(search=league_name, season=season)
        if not leagues:
            leagues = await self.api_client.get_leagues(search=league_name)
        if not leagues:
            return None, []
        if len(leagues) == 1:
            return leagues[0], leagues
        exact = self._pick_exact_match(leagues, league_name, lambda l: (l.get("league", {}) or {}).get("name"))
        if exact:
            return exact, leagues
        return None, leagues

    async def _get_fixture_by_id(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        fixtures = await self.api_client.get_fixtures(fixture_id=fixture_id)
        return fixtures[0] if fixtures else None

    async def _find_fixture(
        self,
        home_team_id: Optional[int],
        away_team_id: Optional[int],
        date_str: Optional[str],
        league_id: Optional[int],
        season: Optional[int],
        intent_name: str,
    ) -> Optional[Dict[str, Any]] | List[Dict[str, Any]]:
        if not home_team_id or not away_team_id:
            return None

        if date_str:
            fixtures = await self.api_client.get_fixtures(
                team_id=home_team_id,
                date=date_str,
                league_id=league_id,
                season=season,
            )
            matches = [fx for fx in fixtures if self._fixture_has_teams(fx, home_team_id, away_team_id)]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return matches
            return None

        mode = self._intent_mode(intent_name)
        if mode == "live":
            fixtures = await self.api_client.get_fixtures(team_id=home_team_id, live="all")
            matches = [fx for fx in fixtures if self._fixture_has_teams(fx, home_team_id, away_team_id)]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return matches

        if mode == "finished":
            fixtures = await self.api_client.get_fixtures(
                team_id=home_team_id,
                last=5,
                league_id=league_id,
                season=season,
            )
            matches = [fx for fx in fixtures if self._fixture_has_teams(fx, home_team_id, away_team_id)]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return matches

        fixtures = await self.api_client.get_fixtures(
            team_id=home_team_id,
            next=5,
            league_id=league_id,
            season=season,
        )
        matches = [fx for fx in fixtures if self._fixture_has_teams(fx, home_team_id, away_team_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return matches

        fixtures = await self.api_client.get_fixtures(
            team_id=home_team_id,
            last=5,
            league_id=league_id,
            season=season,
        )
        matches = [fx for fx in fixtures if self._fixture_has_teams(fx, home_team_id, away_team_id)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return matches
        return None

    def _fixture_has_teams(self, fixture: Dict[str, Any], team_a: int, team_b: int) -> bool:
        teams = fixture.get("teams", {}) or {}
        home_id = (teams.get("home") or {}).get("id")
        away_id = (teams.get("away") or {}).get("id")
        return (home_id == team_a and away_id == team_b) or (home_id == team_b and away_id == team_a)

    def _intent_mode(self, intent_name: str) -> str:
        if intent_name in LIVE_INTENTS:
            return "live"
        if intent_name in FINISHED_INTENTS:
            return "finished"
        return "upcoming"

    def _build_match_context_from_fixture(self, fixture: Dict[str, Any]) -> Dict[str, Any]:
        fixture_block = fixture.get("fixture", {}) or {}
        league_block = fixture.get("league", {}) or {}
        teams_block = fixture.get("teams", {}) or {}
        home_block = teams_block.get("home", {}) or {}
        away_block = teams_block.get("away", {}) or {}

        return {
            "context_type": "match",
            "fixture_id": fixture_block.get("id"),
            "match_date": fixture_block.get("date"),
            "league_id": league_block.get("id"),
            "league_name": league_block.get("name"),
            "competition_name": league_block.get("name"),
            "season": league_block.get("season"),
            "team1_name": home_block.get("name"),
            "team2_name": away_block.get("name"),
        }

    def _resolve_season(self, entities: Dict[str, Any], user_message: str) -> Optional[int]:
        season = entities.get("season")
        if season is not None:
            return self._coerce_int(season)
        match = YEAR_PATTERN.search(user_message or "")
        if match:
            return self._coerce_int(match.group(0))
        return self._current_season_year()

    def _season_from_league_entry(self, league_entry: Dict[str, Any]) -> Optional[int]:
        seasons = league_entry.get("seasons") or []
        current = next((s for s in seasons if s.get("current")), None)
        if current:
            return self._coerce_int(current.get("year"))
        years = [self._coerce_int(s.get("year")) for s in seasons if s.get("year") is not None]
        years = [y for y in years if y]
        return max(years) if years else self._current_season_year()

    def _current_season_year(self) -> int:
        now = datetime.utcnow()
        return now.year if now.month >= 8 else now.year - 1

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        if not date_str:
            return None
        raw = str(date_str).strip()
        lowered = raw.lower()
        if lowered in {"today", "aujourdhui", "aujourd'hui"}:
            return datetime.utcnow().strftime("%Y-%m-%d")
        if lowered in {"tomorrow", "demain"}:
            return (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        if lowered in {"yesterday", "hier"}:
            return (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        match = re.match(r"^(\\d{1,2})[/-](\\d{1,2})[/-](\\d{4})$", raw)
        if match:
            day, month, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        match = re.match(r"^(\\d{4})[/-](\\d{1,2})[/-](\\d{1,2})$", raw)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        if re.match(r"^\\d{4}-\\d{2}-\\d{2}$", raw):
            return raw
        return None

    def _pick_exact_match(
        self,
        options: List[Dict[str, Any]],
        target: str,
        name_getter,
    ) -> Optional[Dict[str, Any]]:
        target_norm = self._normalize_name(target)
        matches = [
            item for item in options if self._normalize_name(name_getter(item)) == target_norm
        ]
        if len(matches) == 1:
            return matches[0]
        return None

    def _pick_player_match(self, options: List[Dict[str, Any]], player_name: str) -> Optional[Dict[str, Any]]:
        if not options:
            return None
        if len(options) == 1:
            return options[0]
        exact = self._pick_exact_match(options, player_name, lambda p: (p.get("player", {}) or {}).get("name"))
        if exact:
            return exact
        return None

    def _player_has_team_id(self, player_entry: Dict[str, Any], team_id: int) -> bool:
        stats = player_entry.get("statistics") or []
        for stat in stats:
            team_block = stat.get("team", {}) or {}
            if team_block.get("id") == team_id:
                return True
        return False

    def _player_has_team_name(self, player_entry: Dict[str, Any], team_name: str) -> bool:
        team_norm = self._normalize_name(team_name)
        stats = player_entry.get("statistics") or []
        for stat in stats:
            team_block = stat.get("team", {}) or {}
            if self._normalize_name(team_block.get("name")) == team_norm:
                return True
        return False

    def _format_team_options(self, teams: List[Dict[str, Any]], limit: int = 3) -> str:
        options = []
        for team_entry in teams[:limit]:
            team = team_entry.get("team", {}) or team_entry
            name = team.get("name")
            country = team.get("country")
            if name and country:
                options.append(f"{name} ({country})")
            elif name:
                options.append(name)
        return ", ".join(options)

    def _format_league_options(self, leagues: List[Dict[str, Any]], limit: int = 3) -> str:
        options = []
        for league_entry in leagues[:limit]:
            league = league_entry.get("league", {}) or {}
            country = league_entry.get("country", {}) or {}
            name = league.get("name")
            country_name = country.get("name")
            if name and country_name:
                options.append(f"{name} ({country_name})")
            elif name:
                options.append(name)
        return ", ".join(options)

    def _format_player_options(self, players: List[Dict[str, Any]], limit: int = 3) -> str:
        options = []
        for player_entry in players[:limit]:
            player = player_entry.get("player", {}) or {}
            name = player.get("name")
            nationality = player.get("nationality")
            stats = (player_entry.get("statistics") or [{}])[0]
            team_block = stats.get("team", {}) or {}
            team_name = team_block.get("name")
            parts = [p for p in [name, team_name, nationality] if p]
            if parts:
                options.append(" - ".join(parts))
        return ", ".join(options)

    def _normalize_name(self, value: Optional[str]) -> str:
        return re.sub(r"\\s+", " ", (value or "")).strip().lower()

    def _coerce_int(self, value: Any) -> Optional[int]:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def _question(self, language: str, key: str, **kwargs: Any) -> str:
        is_en = (language or "fr").lower().startswith("en")
        templates = {
            "match_missing_teams": {
                "fr": "De quel match parles-tu ? Indique les deux equipes et la competition ou la date.",
                "en": "Which match do you mean? Provide both teams and the competition or date.",
            },
            "team_missing": {
                "fr": "Quelle equipe t'interesse ?",
                "en": "Which team are you interested in?",
            },
            "player_missing": {
                "fr": "Quel joueur t'interesse ?",
                "en": "Which player are you interested in?",
            },
            "league_missing": {
                "fr": "Quelle ligue ou competition t'interesse ?",
                "en": "Which league or competition are you interested in?",
            },
            "team_not_found": {
                "fr": "Je ne trouve pas l'equipe '{name}'. Peux-tu preciser le pays ?",
                "en": "I cannot find the team '{name}'. Please specify the country.",
            },
            "player_not_found": {
                "fr": "Je ne trouve pas le joueur '{name}'. Peux-tu preciser le club ou la nationalite ?",
                "en": "I cannot find the player '{name}'. Please specify the club or nationality.",
            },
            "league_not_found": {
                "fr": "Je ne trouve pas la competition '{name}'. Peux-tu preciser le pays ou la saison ?",
                "en": "I cannot find the competition '{name}'. Please specify the country or season.",
            },
            "team_ambiguous": {
                "fr": "Plusieurs equipes pour '{name}': {options}. Precise le pays ou la ligue.",
                "en": "Multiple teams for '{name}': {options}. Specify the country or league.",
            },
            "player_ambiguous": {
                "fr": "Plusieurs joueurs pour '{name}': {options}. Precise le club ou la nationalite.",
                "en": "Multiple players for '{name}': {options}. Specify the club or nationality.",
            },
            "league_ambiguous": {
                "fr": "Plusieurs competitions pour '{name}': {options}. Precise le pays ou la saison.",
                "en": "Multiple competitions for '{name}': {options}. Specify the country or season.",
            },
            "fixture_not_found": {
                "fr": "Je ne trouve pas ce match. Precise les equipes, la date ou la competition.",
                "en": "I cannot find this match. Provide the teams, date, or competition.",
            },
            "fixture_not_found_teams": {
                "fr": "Je ne trouve pas de match {home} vs {away}. Precise la date ou la competition.",
                "en": "I cannot find a match between {home} and {away}. Please specify the date or competition.",
            },
            "fixture_ambiguous": {
                "fr": "Plusieurs matchs {home} vs {away} existent. Quelle date ou competition vises-tu ?",
                "en": "Multiple matches between {home} and {away}. Which date or competition do you mean?",
            },
        }
        template = templates.get(key, {})
        text = template.get("en" if is_en else "fr", "")
        return text.format(**kwargs)


MATCH_INTENTS = {
    "score_live",
    "stats_live",
    "events_live",
    "players_live",
    "lineups_live",
    "result_final",
    "stats_final",
    "events_summary",
    "players_performance",
    "analyse_rencontre",
    "prediction_global",
    "form_analysis",
    "h2h_analysis",
    "stats_comparison",
    "injuries_impact",
    "probable_lineups",
    "odds_analysis",
    "detail_fixture",
    "chronologie_match",
    "compositions_match",
    "stats_equipes_match",
    "stats_joueurs_match",
    "matchs_live_filtre",
    "prochains_ou_derniers_matchs",
    "calendrier_matchs",
    "prochain_match_equipe",
}

PLAYER_INTENTS = {
    "stats_joueur",
    "profil_joueur",
    "stats_joueur_saison_detail",
    "parcours_equipes_joueur",
    "equipes_dun_joueur",
    "transferts",
    "palmares",
    "blessures_precises",
    "indisponibilites_historiques",
}

TEAM_INTENTS = {
    "stats_equipe_saison",
    "info_equipe",
    "saisons_equipe",
    "effectif_equipe",
    "calendrier_equipe",
}

LEAGUE_INTENTS = {
    "classement_ligue",
    "top_performers",
    "top_cartons",
    "calendrier_ligue_saison",
    "journees_competition",
    "referentiel_ligues",
    "referentiel_pays",
    "saisons_disponibles",
    "timezones_disponibles",
    "standings",
    "top_scorers",
    "top_assists",
    "team_stats",
    "next_fixtures",
    "results",
}

LIVE_INTENTS = {
    "score_live",
    "stats_live",
    "events_live",
    "players_live",
    "lineups_live",
}

FINISHED_INTENTS = {
    "result_final",
    "stats_final",
    "events_summary",
    "players_performance",
}
