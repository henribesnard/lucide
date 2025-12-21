"""
Tools exposed to the LLM for API-Football calls.
Each tool returns compact structures to limit prompt size.
"""
from typing import Any, Dict, List
import logging
import time
from datetime import datetime

from backend.api.football_api import FootballAPIClient
from backend.utils.status_mapping import get_status_info

logger = logging.getLogger(__name__)


def _limit_list(items: Any, limit: int = 5) -> Any:
    """Truncate lists to keep payloads compact."""
    if isinstance(items, list):
        return items[:limit]
    return items


def _summarize_country(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": item.get("name"),
        "code": item.get("code"),
        "flag": item.get("flag"),
    }


def _summarize_league(item: Dict[str, Any]) -> Dict[str, Any]:
    league = item.get("league", {}) or {}
    country = item.get("country", {}) or {}
    seasons = item.get("seasons") or []
    current_seasons = [s.get("year") for s in seasons if s.get("current")]
    return {
        "id": league.get("id"),
        "name": league.get("name"),
        "type": league.get("type"),
        "country": country.get("name"),
        "code": country.get("code"),
        "current_seasons": current_seasons[:3],
    }


def _summarize_team(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or item
    venue = item.get("venue", {}) or {}
    return {
        "id": team.get("id"),
        "name": team.get("name"),
        "code": team.get("code"),
        "country": team.get("country"),
        "founded": team.get("founded"),
        "venue": {
            "id": venue.get("id"),
            "name": venue.get("name"),
            "city": venue.get("city"),
            "country": venue.get("country"),
            "capacity": venue.get("capacity"),
        },
    }


def _summarize_venue(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "city": item.get("city"),
        "country": item.get("country"),
        "capacity": item.get("capacity"),
        "surface": item.get("surface"),
    }


def _summarize_fixture(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {})
    league = item.get("league", {})
    teams = item.get("teams", {})
    goals = item.get("goals", {})
    status_info = get_status_info((fixture.get("status") or {}).get("short"))
    return {
        "fixture_id": fixture.get("id"),
        "date": fixture.get("date"),
        "status_code": status_info["code"],
        "status_label": status_info["label"],
        "status_type": status_info["type"],
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
    passes = stats.get("passes", {})
    return {
        "player_id": player.get("id"),
        "name": player.get("name"),
        "team": (games.get("team") or {}).get("name"),
        "position": player.get("position") or (games.get("position")),
        "appearances": games.get("appearences"),
        "minutes": games.get("minutes"),
        "goals": goals.get("total"),
        "assists": passes.get("total"),
        "rating": games.get("rating"),
    }


def _summarize_player_profile(item: Dict[str, Any]) -> Dict[str, Any]:
    player = item.get("player", {}) or {}
    return {
        "id": player.get("id"),
        "name": player.get("name"),
        "firstname": player.get("firstname"),
        "lastname": player.get("lastname"),
        "age": player.get("age"),
        "nationality": player.get("nationality"),
        "height": player.get("height"),
        "weight": player.get("weight"),
        "number": player.get("number"),
        "position": player.get("position"),
    }


def _summarize_squad(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or {}
    players = item.get("players") or []
    return {
        "team": {"id": team.get("id"), "name": team.get("name")},
        "players": [
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "age": p.get("age"),
                "number": p.get("number"),
                "position": p.get("position"),
            }
            for p in players
        ],
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
        "values": _limit_list(values, limit=5),
    }


def _summarize_live_odds(item: Dict[str, Any]) -> Dict[str, Any]:
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
        "updated_at": item.get("update"),
        "bookmaker": main_book.get("name"),
        "bet": first_bet.get("name"),
        "values": _limit_list(values, limit=5),
    }


def _summarize_bookmaker(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": item.get("id"), "name": item.get("name"), "url": item.get("link")}


def _summarize_bet(item: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": item.get("id"), "name": item.get("name"), "group": item.get("group")}


def _summarize_odds_mapping(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {}) or {}
    league = item.get("league", {}) or {}
    return {
        "fixture_id": fixture.get("id"),
        "league_id": league.get("id"),
        "league": league.get("name"),
        "season": league.get("season"),
        "updated_at": item.get("update"),
    }

def _summarize_event(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or {}
    player = item.get("player", {}) or {}
    assist = item.get("assist", {}) or {}
    time = item.get("time", {}) or {}
    return {
        "minute": time.get("elapsed"),
        "team": team.get("name"),
        "player": player.get("name"),
        "assist": assist.get("name"),
        "type": item.get("type"),
        "detail": item.get("detail"),
    }


def _summarize_lineup(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or {}
    coach = item.get("coach", {}) or {}
    start_xi = item.get("startXI") or []
    return {
        "team": team.get("name"),
        "team_id": team.get("id"),
        "formation": item.get("formation"),
        "coach": coach.get("name"),
        "startXI": [
            {
                "id": p.get("player", {}).get("id"),
                "name": p.get("player", {}).get("name"),
                "number": p.get("player", {}).get("number"),
                "pos": p.get("player", {}).get("pos"),
            }
            for p in start_xi
        ],
    }


def _summarize_fixture_statistics(item: Dict[str, Any]) -> Dict[str, Any]:
    stats_list = item.get("statistics") or []
    stats_map = {s.get("type"): s.get("value") for s in stats_list}
    team = item.get("team", {}) or {}
    return {
        "team": team.get("name"),
        "team_id": team.get("id"),
        "stats": stats_map,
    }


def _summarize_fixture_players(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or {}
    players = item.get("players") or []
    simplified: List[Dict[str, Any]] = []
    for player in players:
        pdata = player.get("player", {}) or {}
        stats = (player.get("statistics") or [{}])[0]
        games = stats.get("games", {}) or {}
        goals = stats.get("goals", {}) or {}
        passes = stats.get("passes", {}) or {}
        simplified.append(
            {
                "id": pdata.get("id"),
                "name": pdata.get("name"),
                "number": pdata.get("number"),
                "position": games.get("position"),
                "minutes": games.get("minutes"),
                "rating": games.get("rating"),
                "goals": goals.get("total"),
                "assists": passes.get("goal_assist") or passes.get("assists"),
            }
        )
    return {
        "team": team.get("name"),
        "team_id": team.get("id"),
        "players": _limit_list(simplified, limit=12),
    }


def _summarize_transfer(item: Dict[str, Any]) -> Dict[str, Any]:
    teams = item.get("teams", {}) or {}
    incoming = teams.get("in") or {}
    outgoing = teams.get("out") or {}
    return {
        "date": item.get("date"),
        "type": item.get("type"),
        "in": incoming.get("name"),
        "out": outgoing.get("name"),
    }


def _summarize_coach(item: Dict[str, Any]) -> Dict[str, Any]:
    team = item.get("team", {}) or {}
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "nationality": item.get("nationality"),
        "team": team.get("name"),
    }


def _infer_season(date_str: str | None) -> int:
    """
    Best-effort inference of season when missing:
    - If a date is provided, use its year.
    - Otherwise, use current year (UTC).
    """
    if date_str:
        try:
            return datetime.fromisoformat(date_str).year
        except Exception:
            pass
    return datetime.utcnow().year

# Tool definitions exposed to the LLM
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "analyze_match",
            "description": "Analyse complete d'un match pour les paris sportifs. Collecte toutes les donnees necessaires (25 appels API la premiere fois, 0 ensuite grace au cache) et analyse 8 types de paris: 1X2, buts, tirs, corners, cartons equipe, carton joueur, buteur, passeur. IMPORTANT: Utilise ce tool pour toute question d'analyse de match au lieu des tools classiques.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {
                        "type": "integer",
                        "description": "ID du match a analyser (obligatoire)"
                    },
                    "bet_type": {
                        "type": "string",
                        "description": "Type de pari specifique (optionnel): 1x2, goals, shots, corners, cards_team, card_player, scorer, assister. Si absent, retourne un resume de toutes les analyses.",
                        "enum": ["1x2", "goals", "shots", "corners", "cards_team", "card_player", "scorer", "assister"]
                    }
                },
                "required": ["fixture_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "countries",
            "description": "Liste les pays disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "code": {"type": "string"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leagues",
            "description": "Recherche les ligues/coupes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "country": {"type": "string"},
                    "season": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "code": {"type": "string"},
                    "type": {"type": "string"},
                    "current": {"type": "boolean"},
                    "search": {"type": "string"},
                    "last": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "league_seasons",
            "description": "Liste les saisons disponibles (endpoint leagues/seasons).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "timezones",
            "description": "Liste les timezones supportes.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "teams",
            "description": "Recherche des equipes (id, nom, ligue, pays).",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "country": {"type": "string"},
                    "code": {"type": "string"},
                    "venue_id": {"type": "integer"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_seasons",
            "description": "Liste des saisons jouees par une equipe.",
            "parameters": {
                "type": "object",
                "properties": {"team_id": {"type": "integer"}},
                "required": ["team_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_countries",
            "description": "Liste des pays disposant d'equipes.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
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
            "name": "player_profile",
            "description": "Profil joueur (bio, poste, numero).",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer"},
                    "search": {"type": "string", "description": "Recherche nom"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "player_statistics",
            "description": "Stats detaillees d'un joueur (saison/league/team).",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer"},
                    "player_name": {"type": "string"},
                    "season": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "league_id": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "players_squads",
            "description": "Effectif d'une equipe ou equipes d'un joueur.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "player_id": {"type": "integer"},
                },
                "required": [],
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
            "name": "fixtures_search",
            "description": "Recherche generique de fixtures (league/team/date/from-to/live/next/last).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "date": {"type": "string"},
                    "from_date": {"type": "string"},
                    "to_date": {"type": "string"},
                    "round": {"type": "string"},
                    "status": {"type": "string"},
                    "venue_id": {"type": "integer"},
                    "timezone": {"type": "string"},
                    "live": {"type": "string"},
                    "last": {"type": "integer"},
                    "next": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_rounds",
            "description": "Liste des journees/tours d'une ligue pour une saison.",
            "parameters": {
                "type": "object",
                "properties": {
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "current": {"type": "boolean"},
                },
                "required": ["league_id", "season"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "team_last_fixtures",
            "description": "Recupere les derniers matchs d'une equipe pour analyser la forme recente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "team_id": {"type": "integer"},
                    "count": {
                        "type": "integer",
                        "description": "Nombre de matchs a ramener",
                        "default": 5,
                    },
                },
                "required": ["team_id"],
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
                    "team_id": {"type": "integer"},
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
                    "date": {"type": "string"},
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
                    "from_date": {"type": "string"},
                    "to_date": {"type": "string"},
                    "league_id": {"type": "integer"},
                    "season": {"type": "integer"},
                    "status": {"type": "string"},
                    "venue_id": {"type": "integer"},
                    "timezone": {"type": "string"},
                },
                "required": ["team1_id", "team2_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_events",
            "description": "Evenements d'un match (buts, cartons...).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "player_id": {"type": "integer"},
                    "type": {"type": "string"},
                },
                "required": ["fixture_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_lineups",
            "description": "Compositions d'equipe pour un match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                },
                "required": ["fixture_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_statistics",
            "description": "Statistiques d'equipe pour un match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                },
                "required": ["fixture_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fixture_players",
            "description": "Statistiques joueurs pour un match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                },
                "required": ["fixture_id"],
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
            "name": "top_yellow_cards",
            "description": "Joueurs avec le plus de cartons jaunes.",
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
            "name": "top_red_cards",
            "description": "Joueurs avec le plus de cartons rouges.",
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
                    "fixture_id": {"type": "integer"},
                    "player_id": {"type": "integer"},
                    "date": {"type": "string"},
                    "timezone": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sidelined",
            "description": "Historique des absences (sidelined) pour un joueur ou coach.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer"},
                    "coach_id": {"type": "integer"},
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
                    "timezone": {"type": "string"},
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
    {
        "type": "function",
        "function": {
            "name": "odds_live",
            "description": "Cotes live (en cours) pour un match ou une ligue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fixture_id": {"type": "integer"},
                    "league_id": {"type": "integer"},
                    "bet_id": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "odds_bookmakers",
            "description": "Referentiel des bookmakers disponibles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bookmaker_id": {"type": "integer"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "odds_bets",
            "description": "Referentiel des types de paris (bets).",
            "parameters": {
                "type": "object",
                "properties": {
                    "bet_id": {"type": "integer"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "odds_mapping",
            "description": "Mapping complet des cotes disponibles (fixture/league).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "transfers",
            "description": "Historique des transferts d'un joueur ou d'une equipe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "trophies",
            "description": "Palmares d'un joueur ou coach.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_id": {"type": "integer"},
                    "coach_id": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "coaches",
            "description": "Informations sur les coachs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coach_id": {"type": "integer"},
                    "team_id": {"type": "integer"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "venues",
            "description": "Informations sur les stades.",
            "parameters": {
                "type": "object",
                "properties": {
                    "venue_id": {"type": "integer"},
                    "name": {"type": "string"},
                    "city": {"type": "string"},
                    "country": {"type": "string"},
                    "search": {"type": "string"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "api_status",
            "description": "Etat du quota API-Football (endpoint /status).",
            "parameters": {"type": "object", "properties": {}, "required": []},
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
        start = time.monotonic()
        if name == "countries":
            countries = await api_client.get_countries(
                name=args.get("name"), code=args.get("code"), search=args.get("search")
            )
            return {"countries": [_summarize_country(c) for c in countries]}

        if name == "leagues":
            leagues = await api_client.get_leagues(
                league_id=args.get("league_id"),
                name=args.get("name"),
                country=args.get("country"),
                season=args.get("season"),
                team_id=args.get("team_id"),
                code=args.get("code"),
                type_=args.get("type"),
                current=args.get("current"),
                search=args.get("search"),
                last=args.get("last"),
            )
            return {"leagues": [_summarize_league(lg) for lg in leagues]}

        if name == "league_seasons":
            seasons = await api_client.get_seasons()
            return {"seasons": seasons}

        if name == "timezones":
            timezones = await api_client.get_timezones()
            return {"timezones": timezones}

        if name == "teams":
            teams = await api_client.get_teams(
                team_id=args.get("team_id"),
                name=args.get("name"),
                league_id=args.get("league_id"),
                season=args.get("season"),
                country=args.get("country"),
                code=args.get("code"),
                venue_id=args.get("venue_id"),
                search=args.get("search"),
            )
            return {"teams": [_summarize_team(t) for t in teams]}

        if name == "team_seasons":
            seasons = await api_client.get_team_seasons(args["team_id"])
            return {"seasons": seasons}

        if name == "team_countries":
            countries = await api_client.get_team_countries()
            return {"countries": [_summarize_country(c) for c in countries]}

        if name == "search_team":
            team = await api_client.search_team(args["team_name"])
            return {"team": team} if team else {"message": "Aucune equipe trouvee"}

        if name == "search_player":
            player = await api_client.search_player(
                player_name=args["player_name"], season=args.get("season")
            )
            return {"player": _summarize_player(player)} if player else {"message": "Aucun joueur trouve"}

        if name == "player_profile":
            profiles = await api_client.get_player_profiles(
                player_id=args.get("player_id"), search=args.get("search")
            )
            return {"profiles": [_summarize_player_profile(p) for p in profiles]}

        if name == "player_statistics":
            data = await api_client.get_players(
                player_id=args.get("player_id"),
                search=args.get("player_name"),
                season=args.get("season"),
                team_id=args.get("team_id"),
                league_id=args.get("league_id"),
            )
            items = data.get("response", [])
            return {
                "players": [_summarize_player(it) for it in items],
                "paging": data.get("paging") or {},
            }

        if name == "players_squads":
            squads = await api_client.get_players_squads(
                team_id=args.get("team_id"), player_id=args.get("player_id")
            )
            return {"squads": [_summarize_squad(s) for s in squads]}

        if name == "fixtures_by_date":
            season = args.get("season")
            if args.get("league_id") and not season:
                season = _infer_season(args.get("date"))
            fixtures = await api_client.get_fixtures(
                date=args["date"],
                league_id=args.get("league_id"),
                season=season,
                status=args.get("status"),
            )
            summarized = [_summarize_fixture(fx) for fx in fixtures]
            return {"fixtures": _limit_list(summarized, limit=15)}

        if name == "fixtures_search":
            season = args.get("season")
            if not season:
                if args.get("date"):
                    try:
                        date_obj = datetime.fromisoformat(args["date"])
                        season = date_obj.year if date_obj.month >= 8 else date_obj.year - 1
                    except Exception:
                        now = datetime.utcnow()
                        season = now.year if now.month >= 8 else now.year - 1
                else:
                    now = datetime.utcnow()
                    season = now.year if now.month >= 8 else now.year - 1
            fixtures = await api_client.get_fixtures(
                fixture_id=args.get("fixture_id"),
                league_id=None if args.get("fixture_id") else args.get("league_id"),
                season=None if args.get("fixture_id") else season,
                team_id=None if args.get("fixture_id") else args.get("team_id"),
                date=None if args.get("fixture_id") else args.get("date"),
                from_date=None if args.get("fixture_id") else args.get("from_date"),
                to_date=None if args.get("fixture_id") else args.get("to_date"),
                round_=None if args.get("fixture_id") else args.get("round"),
                status=None if args.get("fixture_id") else args.get("status"),
                venue_id=None if args.get("fixture_id") else args.get("venue_id"),
                timezone=None if args.get("fixture_id") else args.get("timezone"),
                live=None if args.get("fixture_id") else args.get("live"),
                last=None if args.get("fixture_id") else args.get("last"),
                next=None if args.get("fixture_id") else args.get("next"),
            )
            summarized = [_summarize_fixture(fx) for fx in fixtures]
            return {"fixtures": _limit_list(summarized, limit=15)}

        if name == "fixture_rounds":
            rounds = await api_client.get_fixture_rounds(
                league_id=args["league_id"], season=args["season"], current=args.get("current", False)
            )
            return {"rounds": rounds}

        if name == "team_last_fixtures":
            fixtures = await api_client.get_team_last_fixtures(
                team_id=args["team_id"], n=args.get("count", 5)
            )
            summarized = [_summarize_fixture(fx) for fx in fixtures]
            return {"fixtures": _limit_list(summarized, limit=10)}

        if name == "team_next_fixtures":
            fixtures = await api_client.get_team_next_fixtures(
                team_id=args["team_id"], n=args.get("count", 1)
            )
            summarized = [_summarize_fixture(fx) for fx in fixtures]
            return {"fixtures": _limit_list(summarized, limit=10)}

        if name == "live_fixtures":
            fixtures = await api_client.get_live_fixtures()
            summarized = [_summarize_fixture(fx) for fx in fixtures]
            return {"fixtures": _limit_list(summarized, limit=15)}

        if name == "standings":
            standings = await api_client.get_standings(
                season=args["season"], league_id=args["league_id"], team_id=args.get("team_id")
            )
            table: List[Dict[str, Any]] = []
            for block in standings:
                table.extend(block.get("league", {}).get("standings", [[]])[0])
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "standings": [_summarize_standing(row) for row in table],
            }

        if name == "team_statistics":
            stats = await api_client.get_team_statistics(
                team_id=args["team_id"],
                season=args["season"],
                league_id=args["league_id"],
                date=args.get("date"),
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "team_id": args.get("team_id"),
                "statistics": stats,
            }

        if name == "head_to_head":
            games = await api_client.get_head_to_head(
                team1_id=args["team1_id"],
                team2_id=args["team2_id"],
                last=args.get("last", 5),
                from_date=args.get("from_date"),
                to_date=args.get("to_date"),
                league_id=args.get("league_id"),
                season=args.get("season"),
                status=args.get("status"),
                venue_id=args.get("venue_id"),
                timezone=args.get("timezone"),
            )
            summarized = [_summarize_fixture(fx) for fx in games]
            return {"fixtures": _limit_list(summarized, limit=10)}
        if name == "fixture_events":
            events = await api_client.get_fixture_events(
                fixture_id=args["fixture_id"],
                team_id=args.get("team_id"),
                player_id=args.get("player_id"),
                type_=args.get("type"),
            )
            return {"events": _limit_list([_summarize_event(ev) for ev in events], limit=40)}

        if name == "fixture_lineups":
            lineups = await api_client.get_fixture_lineups(
                fixture_id=args["fixture_id"], team_id=args.get("team_id")
            )
            return {"lineups": [_summarize_lineup(lu) for lu in lineups]}

        if name == "fixture_statistics":
            stats = await api_client.get_fixture_statistics(
                fixture_id=args["fixture_id"], team_id=args.get("team_id")
            )
            return {"statistics": [_summarize_fixture_statistics(st) for st in stats]}

        if name == "fixture_players":
            players = await api_client.get_fixture_player_statistics(
                fixture_id=args["fixture_id"], team_id=args.get("team_id")
            )
            return {"players": _limit_list([_summarize_fixture_players(p) for p in players], limit=4)}

        if name == "top_scorers":
            scorers = await api_client.get_top_scorers(
                league_id=args["league_id"], season=args["season"]
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "top_scorers": _limit_list([_summarize_player(item) for item in scorers], limit=10),
            }

        if name == "top_assists":
            assists = await api_client.get_top_assists(
                league_id=args["league_id"], season=args["season"]
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "top_assists": _limit_list([_summarize_player(item) for item in assists], limit=10),
            }

        if name == "top_yellow_cards":
            cards = await api_client.get_top_yellow_cards(
                league_id=args["league_id"], season=args["season"]
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "top_yellow_cards": _limit_list([_summarize_player(item) for item in cards], limit=10),
            }

        if name == "top_red_cards":
            cards = await api_client.get_top_red_cards(
                league_id=args["league_id"], season=args["season"]
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "top_red_cards": _limit_list([_summarize_player(item) for item in cards], limit=10),
            }

        if name == "injuries":
            injuries = await api_client.get_injuries(
                league_id=args.get("league_id"),
                season=args.get("season"),
                fixture_id=args.get("fixture_id"),
                team_id=args.get("team_id"),
                player_id=args.get("player_id"),
                date=args.get("date"),
                timezone=args.get("timezone"),
            )
            return {
                "season": args.get("season"),
                "league_id": args.get("league_id"),
                "team_id": args.get("team_id"),
                "fixture_id": args.get("fixture_id"),
                "injuries": _limit_list([_summarize_injury(item) for item in injuries], limit=15),
            }

        if name == "sidelined":
            sidelined = await api_client.get_sidelined(
                player_id=args.get("player_id"), coach_id=args.get("coach_id")
            )
            return {"sidelined": _limit_list(sidelined, limit=15)}

        if name == "predictions":
            prediction = await api_client.get_predictions(args["fixture_id"])
            return {"prediction": _summarize_prediction(prediction) if prediction else {}}

        if name == "odds_by_date":
            odds = await api_client.get_odds(
                date=args["date"],
                league_id=args.get("league_id"),
                season=args.get("season"),
                timezone=args.get("timezone"),
            )
            return {"odds": _limit_list([_summarize_odds(item) for item in odds], limit=8)}

        if name == "odds_by_fixture":
            odds = await api_client.get_odds(fixture_id=args["fixture_id"])
            return {"odds": _limit_list([_summarize_odds(item) for item in odds], limit=8)}

        if name == "odds_live":
            odds = await api_client.get_odds_live(
                fixture_id=args.get("fixture_id"), league_id=args.get("league_id"), bet_id=args.get("bet_id")
            )
            return {"odds": _limit_list([_summarize_live_odds(item) for item in odds], limit=8)}

        if name == "odds_bookmakers":
            bookmakers = await api_client.get_bookmakers(
                bookmaker_id=args.get("bookmaker_id"), search=args.get("search")
            )
            return {"bookmakers": _limit_list([_summarize_bookmaker(b) for b in bookmakers], limit=10)}

        if name == "odds_bets":
            bets = await api_client.get_bets(bet_id=args.get("bet_id"), search=args.get("search"))
            return {"bets": _limit_list([_summarize_bet(b) for b in bets], limit=15)}

        if name == "odds_mapping":
            mapping = await api_client.get_odds_mapping()
            return {"mapping": _limit_list([_summarize_odds_mapping(item) for item in mapping], limit=15)}

        if name == "transfers":
            transfers = await api_client.get_transfers(
                player_id=args.get("player_id"), team_id=args.get("team_id")
            )
            simplified: List[Dict[str, Any]] = []
            for t in transfers:
                simplified.extend([_summarize_transfer(tr) for tr in t.get("transfers", [])])
            return {"transfers": _limit_list(simplified, limit=15)}

        if name == "trophies":
            trophies = await api_client.get_trophies(
                player_id=args.get("player_id"), coach_id=args.get("coach_id")
            )
            return {"trophies": trophies}

        if name == "coaches":
            coaches = await api_client.get_coaches(
                coach_id=args.get("coach_id"), team_id=args.get("team_id"), search=args.get("search")
            )
            return {"coaches": [_summarize_coach(c) for c in coaches]}

        if name == "venues":
            venues = await api_client.get_venues(
                venue_id=args.get("venue_id"),
                name=args.get("name"),
                city=args.get("city"),
                country=args.get("country"),
                search=args.get("search"),
            )
            return {"venues": [_summarize_venue(v) for v in venues]}

        if name == "api_status":
            status = await api_client.get_status()
            return {"status": status}

        return {"error": f"Tool {name} is not implemented"}

    except Exception as exc:
        logger.error(f"Tool execution error for {name}: {exc}", exc_info=True)
        return {"error": str(exc)}
    finally:
        duration = time.monotonic() - start
        logger.info(f"Tool {name} executed in {duration:.3f}s with args={args}")
