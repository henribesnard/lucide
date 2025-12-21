"""
Referentiel des compétitions internationales (ID API-Football vérifiés).
"""

from typing import Dict, Any, Optional

INTERNATIONAL_COMPETITIONS: Dict[str, Dict[str, Any]] = {
    # UEFA (Europe)
    "UEFA": {
        "display_name": "UEFA",
        "full_name": "Union of European Football Associations",
        "flag": "EU",
        "competitions": [
            {"id": 2, "name": "UEFA Champions League"},
            {"id": 3, "name": "UEFA Europa League"},
            {"id": 848, "name": "UEFA Europa Conference League"},
            {"id": 5, "name": "UEFA Nations League"},
            {"id": 4, "name": "Euro Championship"},
            {"id": 531, "name": "UEFA Super Cup"},
        ],
    },

    # CAF (Afrique)
    "CAF": {
        "display_name": "CAF",
        "full_name": "Confédération Africaine de Football",
        "flag": "CAF",
        "competitions": [
            {"id": 12, "name": "CAF Champions League"},
            {"id": 20, "name": "CAF Confederation Cup"},
            {"id": 6, "name": "Africa Cup of Nations"},
            {"id": 19, "name": "African Nations Championship"},
        ],
    },

    # CONMEBOL (Amérique du Sud)
    "CONMEBOL": {
        "display_name": "CONMEBOL",
        "full_name": "Confederación Sudamericana de Fútbol",
        "flag": "CONMEBOL",
        "competitions": [
            {"id": 13, "name": "CONMEBOL Libertadores"},
            {"id": 11, "name": "CONMEBOL Sudamericana"},
            {"id": 9, "name": "Copa America"},
            {"id": 14, "name": "Recopa Sudamericana"},
        ],
    },

    # CONCACAF
    "CONCACAF": {
        "display_name": "CONCACAF",
        "full_name": "Confederation of North, Central America and Caribbean Association Football",
        "flag": "CONCACAF",
        "competitions": [
            {"id": 16, "name": "CONCACAF Champions League"},
            {"id": 22, "name": "CONCACAF Gold Cup"},
            {"id": 536, "name": "CONCACAF Nations League"},
        ],
    },

    # AFC (Asie)
    "AFC": {
        "display_name": "AFC",
        "full_name": "Asian Football Confederation",
        "flag": "AFC",
        "competitions": [
            {"id": 17, "name": "AFC Champions League"},
            {"id": 18, "name": "AFC Cup"},
            {"id": 7, "name": "Asian Cup"},
        ],
    },

    # OFC (Océanie)
    "OFC": {
        "display_name": "OFC",
        "full_name": "Oceania Football Confederation",
        "flag": "OFC",
        "competitions": [
            {"id": 27, "name": "OFC Champions League"},
            {"id": 806, "name": "OFC Nations Cup"},
        ],
    },

    # FIFA (Mondial)
    "FIFA": {
        "display_name": "FIFA",
        "full_name": "Fédération Internationale de Football Association",
        "flag": "FIFA",
        "competitions": [
            {"id": 1, "name": "FIFA World Cup"},
            {"id": 15, "name": "FIFA Club World Cup"},
            {"id": 480, "name": "FIFA Confederations Cup"},
        ],
    },
}


def get_confederation_for_league(league_id: int, league_name: str) -> Optional[str]:
    """
    Retourne la confédération d'une ligue basée sur son ID ou son nom.
    """
    for confederation_code, data in INTERNATIONAL_COMPETITIONS.items():
        for comp in data["competitions"]:
            if comp["id"] == league_id or league_name.lower() in comp["name"].lower():
                return confederation_code
    return None
