"""
Intent classifier for user questions.
Maps user intents to specific API endpoints needed to answer the question.
"""

from typing import List, Dict, Any, Optional, Union
import re
import logging

from backend.context.context_types import MatchStatus, LeagueStatus, ContextType

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Classifies user question intent to determine which API endpoints are needed."""

    # Intent patterns for live matches
    LIVE_MATCH_INTENTS = {
        "score_live": {
            "keywords": ["score", "résultat", "combien", "mène", "gagne", "qui gagne"],
            "endpoints": ["fixtures"],
        },
        "stats_live": {
            "keywords": ["statistiques", "stats", "possession", "tirs", "corners", "fautes"],
            "endpoints": ["fixtures", "fixtures/statistics"],
        },
        "events_live": {
            "keywords": ["événements", "events", "buts", "cartons", "remplacements", "qui a marqué"],
            "endpoints": ["fixtures", "fixtures/events"],
        },
        "players_live": {
            "keywords": ["joueurs", "buteur", "passeur", "meilleur joueur", "rating", "note"],
            "endpoints": ["fixtures", "fixtures/players"],
        },
        "lineups_live": {
            "keywords": ["composition", "lineup", "titulaires", "remplaçants", "formation"],
            "endpoints": ["fixtures", "fixtures/lineups"],
        },
    }

    # Intent patterns for finished matches
    FINISHED_MATCH_INTENTS = {
        "result_final": {
            "keywords": ["résultat", "score final", "qui a gagné", "victoire"],
            "endpoints": ["fixtures"],
        },
        "stats_final": {
            "keywords": ["statistiques", "stats", "possession", "tirs", "corners"],
            "endpoints": ["fixtures", "fixtures/statistics"],
        },
        "events_summary": {
            "keywords": ["résumé", "déroulement", "événements", "buts", "cartons"],
            "endpoints": ["fixtures", "fixtures/events"],
        },
        "players_performance": {
            "keywords": ["performance", "joueurs", "buteur", "homme du match", "rating"],
            "endpoints": ["fixtures", "fixtures/players"],
        },
        "match_analysis": {
            "keywords": ["analyse", "analyse du match", "comment"],
            "endpoints": ["fixtures", "fixtures/statistics", "fixtures/events"],
        },
    }

    # Intent patterns for upcoming matches
    UPCOMING_MATCH_INTENTS = {
        "prediction_global": {
            "keywords": [
                "prédiction", "pronostic", "qui va gagner", "favori", "chances",
                "prévision", "analyse globale", "probabilité"
            ],
            "endpoints": ["predictions"],
        },
        "form_analysis": {
            "keywords": ["forme", "série", "derniers matchs", "dynamique", "récents résultats"],
            "endpoints": ["teams/statistics"],
        },
        "h2h_analysis": {
            "keywords": ["h2h", "head to head", "historique", "confrontations", "précédentes rencontres"],
            "endpoints": ["fixtures/headtohead"],
        },
        "stats_comparison": {
            "keywords": ["comparaison", "comparer", "statistiques équipes", "vs"],
            "endpoints": ["teams/statistics"],
        },
        "injuries_impact": {
            "keywords": ["blessés", "absents", "suspendus", "indisponibles", "injuries"],
            "endpoints": ["injuries"],
        },
        "probable_lineups": {
            "keywords": ["composition probable", "équipe probable", "qui va jouer"],
            "endpoints": ["predictions"],
        },
        "odds_analysis": {
            "keywords": ["cotes", "odds", "bookmakers", "paris"],
            "endpoints": ["odds"],
        },
    }

    # Intent patterns for league context
    LEAGUE_INTENTS = {
        "standings": {
            "keywords": ["classement", "ranking", "position", "table", "standings"],
            "endpoints": ["standings"],
        },
        "top_scorers": {
            "keywords": ["meilleurs buteurs", "top scorers", "buteurs", "goals"],
            "endpoints": ["players/topscorers"],
        },
        "top_assists": {
            "keywords": ["meilleurs passeurs", "top assists", "passeurs", "assists"],
            "endpoints": ["players/topassists"],
        },
        "team_stats": {
            "keywords": ["statistiques équipe", "stats équipe", "performance équipe"],
            "endpoints": ["teams/statistics"],
        },
        "next_fixtures": {
            "keywords": ["prochains matchs", "prochaine journée", "calendrier", "fixtures"],
            "endpoints": ["fixtures"],
        },
        "results": {
            "keywords": ["résultats", "derniers matchs", "dernière journée"],
            "endpoints": ["fixtures"],
        },
    }

    @classmethod
    def classify_intent(
        cls,
        question: str,
        context_type: ContextType,
        status: Optional[Union[MatchStatus, LeagueStatus]] = None
    ) -> Dict[str, Any]:
        """
        Classify the intent of a user question.

        Args:
            question: The user's question
            context_type: The type of context (match or league)
            status: The status of the match or league

        Returns:
            Dict with:
                - intent: The classified intent name
                - endpoints: List of endpoints needed
                - confidence: Confidence score (0-1)
        """
        question_lower = question.lower()

        # Select the appropriate intent patterns based on context
        if context_type == ContextType.LEAGUE:
            intent_patterns = cls.LEAGUE_INTENTS
        elif context_type == ContextType.MATCH:
            if status == MatchStatus.LIVE:
                intent_patterns = cls.LIVE_MATCH_INTENTS
            elif status == MatchStatus.FINISHED:
                intent_patterns = cls.FINISHED_MATCH_INTENTS
            elif status == MatchStatus.UPCOMING:
                intent_patterns = cls.UPCOMING_MATCH_INTENTS
            else:
                logger.warning(f"Unknown match status: {status}, using upcoming intents")
                intent_patterns = cls.UPCOMING_MATCH_INTENTS
        else:
            logger.warning(f"Unknown context type: {context_type}")
            return {
                "intent": "unknown",
                "endpoints": [],
                "confidence": 0.0
            }

        # Find the best matching intent
        best_match = None
        best_score = 0

        for intent_name, intent_data in intent_patterns.items():
            score = 0
            for keyword in intent_data["keywords"]:
                if keyword.lower() in question_lower:
                    # Weight longer keywords more heavily
                    score += len(keyword.split())

            if score > best_score:
                best_score = score
                best_match = {
                    "intent": intent_name,
                    "endpoints": intent_data["endpoints"],
                    "confidence": min(score / len(question.split()), 1.0)
                }

        if best_match:
            return best_match

        # Fallback based on context
        if context_type == ContextType.LEAGUE:
            return {
                "intent": "standings",
                "endpoints": ["standings"],
                "confidence": 0.3
            }
        elif status == MatchStatus.LIVE:
            return {
                "intent": "score_live",
                "endpoints": ["fixtures"],
                "confidence": 0.3
            }
        elif status == MatchStatus.FINISHED:
            return {
                "intent": "result_final",
                "endpoints": ["fixtures"],
                "confidence": 0.3
            }
        else:  # UPCOMING
            return {
                "intent": "prediction_global",
                "endpoints": ["predictions"],
                "confidence": 0.3
            }

    @classmethod
    def get_all_intents(cls) -> Dict[str, List[str]]:
        """
        Get all available intents organized by category.

        Returns:
            Dict with intent categories and their intent names
        """
        return {
            "live_match": list(cls.LIVE_MATCH_INTENTS.keys()),
            "finished_match": list(cls.FINISHED_MATCH_INTENTS.keys()),
            "upcoming_match": list(cls.UPCOMING_MATCH_INTENTS.keys()),
            "league": list(cls.LEAGUE_INTENTS.keys()),
        }
