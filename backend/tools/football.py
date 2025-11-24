"""
Tools exposed to the LLM for API-Football calls.
Each tool returns compact structures to limit prompt size.
"""
from typing import Any, Dict, List
import logging

from backend.api.football_api import FootballAPIClient

logger = logging.getLogger(__name__)


def _summarize_fixture(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {})
    league = item.get("league", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})
    return {
        "fixture_id": fixture.get("id"),
        "date": fixture.get("date"),
        "status": (fixture.get("status") or {}).get("short"),
        "venue": (fixture.get("venue") or {}).get("name"),
        "league": {
            "id": league.get("id"),
            "name": league.get("name"),
            "season": league.get("season"),
        },
        "home": {
            "id": (teams.get("home") or {}).get("id"),
            "name": (teams.get("home") or {}).get("name"),
            "goals": goals.get("home"),
        },
        "away": {
            "id": (teams.get("away") or {}).get("id"),
            "name": (teams.get("away") or {}).get("name"),
            "goals": goals.get("away"),
        },
    }


def _summarize_standing(entry: Dict[str, Any]) -> Dict[str, Any]:
    team = entry.get("team", {})
    stats = entry.get("all", {})
    goals = entry.get("goals", {}) or {}
    return {
        "position": entry.get("rank"),
        "team_id": team.get("id"),
        "team": team.get("name"),
        "points": entry.get("points"),
        "played": stats.get("played"),
        "wins": stats.get("win"),
        "draws": stats.get("draw"),
        "losses": stats.get("lose"),
        "goals_for": goals.get("for"),
        "goals_against": goals.get("against"),
        "form": entry.get("form"),
    }


def _summarize_player(item: Dict[str, Any]) -> Dict[str, Any]:
    if not item:
        return {}
    player = item.get("player", {})
    stats = (item.get("statistics") or [{}])[0] if item.get("statistics") else {}
    games = stats.get("games", {})
    goals = stats.get("goals", {})
    assists = stats.get("passes", {})
    return {
        "player_id": player.get("id"),
        "name": player.get("name"),
        "team": (games.get("team") or {}).get("name"),
        "position": player.get("position") or (games.get("position")),
        "appearances": games.get("appearences"),
        "minutes": games.get("minutes"),
        "goals": goals.get("total"),
        "assists": assists.get("total"),
    }


def _summarize_injury(item: Dict[str, Any]) -> Dict[str, Any]:
    player = item.get("player", {})
    team = item.get("team", {})
    return {
        "player": player.get("name"),
        "team": team.get("name"),
        "type": item.get("type"),
        "reason": item.get("reason"),
        "fixture": item.get("fixture"),
    }


def _summarize_prediction(item: Dict[str, Any]) -> Dict[str, Any]:
    if not item:
        return {}
    predictions = item.get("predictions", {})
    comparison = item.get("comparison", {})
    teams = item.get("teams", {})
    return {
        "winner": (predictions.get("winner") or {}).get("name"),
        "advice": predictions.get("advice"),
        "percent": predictions.get("percent"),
        "comparison": comparison,
        "teams": {
            "home": (teams.get("home") or {}).get("name"),
            "away": (teams.get("away") or {}).get("name"),
        },
    }


def _summarize_odds(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {})
    league = item.get("league", {})
    bookmakers = item.get("bookmakers") or []
    main_book = bookmakers[0] if bookmakers else {}
    bets = main_book.get("bets") or []
    first_bet = bets[0] if bets else {}
    values = first_bet.get("values") or []
    return {
        "fixture_id": fixture.get("id"),
        "league": league.get("name"),
        "bookmaker": main_book.get("name"),
        "bet": first_bet.get("name"),
        "values": values[:5],
    }


# Tool definitions exposed to the LLM
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_team",
            "description": "Trouve une equipe par son nom et renvoie l'id et les infos basiques.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_name": {"type": "string", "description": "Nom complet ou acronyme."}
                },
                "required": ["team_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_player",
            "description": "Trouve un joueur par son nom (optionnellement saison).",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_name": {"type": "string"},
                    "season": {"type": "integer", "description": "Annee de la saison, ex 2024"},
                },
                "required": ["player_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixtures_by_date",
            "description": "Liste les matchs d'une date, optionnellement filtres par ligue ou statut.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "status": {"type": "string", "description": "FT, NS, LIVE..."},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_next_fixtures",
            "description": "Recupere les prochains matchs d'une equipe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "count": {"type": "integer", "description": "Nombre de matchs a ramener", "default": 1},
                },
                "required": ["team_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "live_fixtures",
            "description": "Liste tous les matchs en direct.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "standings",
            "description": "Classement d'une ligue pour une saison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": ["league_id", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_statistics",
            "description": "Statistiques saison d'une equipe pour une ligue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": ["team_id", "league_id", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "head_to_head",
            "description": "Historique des confrontations entre deux equipes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team1_id": {"type": "integer"},
                    "team2_id": {"type": "integer"},
                    "last": {"type": "integer", "description": "Nombre de derniers matchs"},
                },
                "required": ["team1_id", "team2_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_scorers",
            "description": "Meilleurs buteurs d'une ligue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": ["league_id", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_assists",
            "description": "Meilleurs passeurs d'une ligue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": ["league_id", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "injuries",
            "description": "Liste des blessures/suspensions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predictions",
            "description": "Predictions statistiques pour un match (fixture id).",
            "parameters": {
                "type": "object",
                "properties": {"fixture_id": {"type": "integer"}},
                "required": ["fixture_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "odds_by_date",
            "description": "Cotes pre-match pour une date et une ligue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "odds_by_fixture",
            "description": "Cotes pre-match pour un match precis.",
            "parameters": {
                "type": "object",
                "properties": {"fixture_id": {"type": "integer"}},
                "required": ["fixture_id"],
            },
        },
    },
]


async def execute_tool(
    api_client: FootballAPIClient, name: str, args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Executes the tool by name using the shared FootballAPIClient.
    All outputs are compacted before being returned to the LLM.
    """
    try:
        if name == "search_team":
            team = await api_client.search_team(args["team_name"])
            return {"team": team} if team else {"message": "Aucune equipe trouvee"}

        if name == "search_player":
            player = await api_client.search_player(
                player_name=args["player_name"], season=args.get("season")
            )
            return {"player": _summarize_player(player)} if player else {"message": "Aucun joueur trouve"}

        if name == "fixtures_by_date":
            fixtures = await api_client.get_fixtures(
                date=args["date"],
                league_id=args.get("league_id"),
                season=args.get("season"),
                status=args.get("status"),
            )
            return {"fixtures": [_summarize_fixture(fx) for fx in fixtures]}

        if name == "team_next_fixtures":
            fixtures = await api_client.get_team_next_fixtures(
                team_id=args["team_id"], n=args.get("count", 1)
            )
            return {"fixtures": [_summarize_fixture(fx) for fx in fixtures]}

        if name == "live_fixtures":
            fixtures = await api_client.get_live_fixtures()
            return {"fixtures": [_summarize_fixture(fx) for fx in fixtures]}

        if name == "standings":
            standings = await api_client.get_standings(
                season=args["season"], league_id=args["league_id"]
            )
            table = []
            for block in standings:
                table.extend(block.get("league", {}).get("standings", [[]])[0])
            return {"standings": [_summarize_standing(row) for row in table]}

        if name == "team_statistics":
            stats = await api_client.get_team_statistics(
                team_id=args["team_id"],
                season=args["season"],
                league_id=args["league_id"],
            )
            return {"statistics": stats}

        if name == "head_to_head":
            games = await api_client.get_head_to_head(
                team1_id=args["team1_id"],
                team2_id=args["team2_id"],
                last=args.get("last", 5),
            )
            return {"fixtures": [_summarize_fixture(fx) for fx in games]}

        if name == "top_scorers":
            scorers = await api_client.get_top_scorers(
                league_id=args["league_id"], season=args["season"]
            )
            return {"top_scorers": [_summarize_player(item) for item in scorers]}

        if name == "top_assists":
            assists = await api_client.get_top_assists(
                league_id=args["league_id"], season=args["season"]
            )
            return {"top_assists": [_summarize_player(item) for item in assists]}

        if name == "injuries":
            injuries = await api_client.get_injuries(
                league_id=args.get("league_id"),
                season=args.get("season"),
                team_id=args.get("team_id"),
            )
            return {"injuries": [_summarize_injury(item) for item in injuries]}

        if name == "predictions":
            prediction = await api_client.get_predictions(args["fixture_id"])
            return {"prediction": _summarize_prediction(prediction) if prediction else {}}

        if name == "odds_by_date":
            odds = await api_client.get_odds(
                date=args["date"],
                league_id=args.get("league_id"),
                season=args.get("season"),
            )
            return {"odds": [_summarize_odds(item) for item in odds]}

        if name == "odds_by_fixture":
            odds = await api_client.get_odds(fixture_id=args["fixture_id"])
            return {"odds": [_summarize_odds(item) for item in odds]}

        return {"error": f"Tool {name} is not implemented"}

    except Exception as exc:
        logger.error(f"Tool execution error for {name}: {exc}", exc_info=True)
        return {"error": str(exc)}
