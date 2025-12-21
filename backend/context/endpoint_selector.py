"""
Endpoint selector - determines which API endpoints to call based on intent.
"""

from typing import List, Dict, Any, Optional, Union
import logging

from backend.context.context_types import MatchStatus, LeagueStatus, ContextType
from backend.context.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class EndpointSelector:
    """Selects the minimal set of API endpoints needed to answer a question."""

    # Maximum number of endpoints to call for a single question
    MAX_ENDPOINTS = 3

    @classmethod
    def select_endpoints(
        cls,
        intent: str,
        context_type: ContextType,
        status: Optional[Union[MatchStatus, LeagueStatus]] = None,
        explicit_endpoints: Optional[List[str]] = None
    ) -> List[str]:
        """
        Select the endpoints to call based on the classified intent.

        Args:
            intent: The classified intent name
            context_type: The type of context (match or league)
            status: The status of the match or league
            explicit_endpoints: Optional explicit list of endpoints from intent classifier

        Returns:
            List of endpoint names to call (max MAX_ENDPOINTS)
        """
        # If explicit endpoints provided, use those (already determined by intent classifier)
        if explicit_endpoints:
            return explicit_endpoints[:cls.MAX_ENDPOINTS]

        # Fallback: determine endpoints based on intent and status
        if context_type == ContextType.LEAGUE:
            return cls._select_league_endpoints(intent)
        elif context_type == ContextType.MATCH:
            if status == MatchStatus.LIVE:
                return cls._select_live_match_endpoints(intent)
            elif status == MatchStatus.FINISHED:
                return cls._select_finished_match_endpoints(intent)
            elif status == MatchStatus.UPCOMING:
                return cls._select_upcoming_match_endpoints(intent)

        logger.warning(f"Could not select endpoints for intent {intent}, context {context_type}, status {status}")
        return []

    @classmethod
    def _select_live_match_endpoints(cls, intent: str) -> List[str]:
        """Select endpoints for live matches."""
        endpoints_map = {
            "score_live": ["fixtures"],
            "stats_live": ["fixtures", "fixtures/statistics"],
            "events_live": ["fixtures", "fixtures/events"],
            "players_live": ["fixtures", "fixtures/players"],
            "lineups_live": ["fixtures", "fixtures/lineups"],
        }
        return endpoints_map.get(intent, ["fixtures"])

    @classmethod
    def _select_finished_match_endpoints(cls, intent: str) -> List[str]:
        """Select endpoints for finished matches."""
        endpoints_map = {
            "result_final": ["fixtures"],
            "stats_final": ["fixtures", "fixtures/statistics"],
            "events_summary": ["fixtures", "fixtures/events"],
            "players_performance": ["fixtures", "fixtures/players"],
            "analyse_rencontre": ["fixtures", "fixtures/statistics", "fixtures/events"],
        }
        return endpoints_map.get(intent, ["fixtures"])

    @classmethod
    def _select_upcoming_match_endpoints(cls, intent: str) -> List[str]:
        """Select endpoints for upcoming matches."""
        endpoints_map = {
            "prediction_global": ["predictions"],
            "form_analysis": ["teams/statistics"],
            "h2h_analysis": ["fixtures/headtohead"],
            "stats_comparison": ["teams/statistics"],
            "injuries_impact": ["injuries"],
            "probable_lineups": ["predictions"],
            "odds_analysis": ["odds"],
        }
        return endpoints_map.get(intent, ["predictions"])

    @classmethod
    def _select_league_endpoints(cls, intent: str) -> List[str]:
        """Select endpoints for league context."""
        endpoints_map = {
            "standings": ["standings"],
            "top_scorers": ["players/topscorers"],
            "top_assists": ["players/topassists"],
            "team_stats": ["teams/statistics"],
            "next_fixtures": ["fixtures"],
            "results": ["fixtures"],
        }
        return endpoints_map.get(intent, ["standings"])

    @classmethod
    def should_use_cached_data(
        cls,
        intent: str,
        context_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if cached context data is sufficient to answer the question.

        Args:
            intent: The classified intent
            context_data: The cached context data

        Returns:
            True if cached data can be used, False if new API calls needed
        """
        if not context_data:
            return False

        # Check if the required data for this intent already exists in context
        required_keys_map = {
            "score_live": ["fixture"],
            "stats_live": ["fixture", "statistics"],
            "events_live": ["fixture", "events"],
            "players_live": ["fixture", "players"],
            "lineups_live": ["fixture", "lineups"],
            "result_final": ["fixture"],
            "stats_final": ["fixture", "statistics"],
            "events_summary": ["fixture", "events"],
            "players_performance": ["fixture", "players"],
            "standings": ["standings"],
            "top_scorers": ["topscorers"],
            "prediction_global": ["predictions"],
        }

        required_keys = required_keys_map.get(intent, [])
        if not required_keys:
            return False

        # Check if all required keys exist in cached data
        return all(key in context_data for key in required_keys)

    @classmethod
    def get_endpoint_priority(cls, endpoint: str, intent: str) -> int:
        """
        Get the priority of an endpoint for a given intent (lower = higher priority).

        Args:
            endpoint: The endpoint name
            intent: The intent name

        Returns:
            Priority score (0 = highest priority)
        """
        # Core fixture data is always highest priority
        if endpoint == "fixtures":
            return 0

        # Predictions are high priority for upcoming matches
        if endpoint == "predictions" and "prediction" in intent:
            return 1

        # Statistics are important for analysis
        if "statistics" in endpoint:
            return 2

        # Everything else has lower priority
        return 3
