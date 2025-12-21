"""
Configuration des ligues favorites à afficher en priorité.
"""

from typing import List, Dict

FAVORITE_LEAGUES: List[Dict[str, object]] = [
    # Top 5 européennes
    {"id": 39, "name": "Premier League", "country": "England"},
    {"id": 140, "name": "La Liga", "country": "Spain"},
    {"id": 61, "name": "Ligue 1", "country": "France"},
    {"id": 135, "name": "Serie A", "country": "Italy"},
    {"id": 78, "name": "Bundesliga", "country": "Germany"},

    # Compétitions internationales majeures
    {"id": 2, "name": "UEFA Champions League", "country": "World"},
    {"id": 3, "name": "UEFA Europa League", "country": "World"},
    {"id": 6, "name": "Africa Cup of Nations", "country": "World"},
    {"id": 1, "name": "FIFA World Cup", "country": "World"},

    # Autres ligues importantes
    {"id": 71, "name": "Serie A", "country": "Brazil"},
    {"id": 128, "name": "Liga Profesional", "country": "Argentina"},
]


def is_favorite_league(league_id: int) -> bool:
    """Check if a league is in favorites."""
    return any(fav["id"] == league_id for fav in FAVORITE_LEAGUES)


def get_favorite_ids() -> List[int]:
    """Get list of favorite league IDs."""
    return [int(fav["id"]) for fav in FAVORITE_LEAGUES]
