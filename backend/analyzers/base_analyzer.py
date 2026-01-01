"""
Base Analyzer - Abstract class for all bet type analyzers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
import logging

from backend.store.schemas import BetAnalysisData

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers

    Each analyzer is responsible for:
    - Defining required data sources
    - Calculating indicators for a specific bet type
    - Checking data coverage
    """

    @property
    @abstractmethod
    def bet_type(self) -> str:
        """Type of bet analyzed (1x2, goals, shots, etc.)"""
        pass

    @property
    @abstractmethod
    def required_sources(self) -> List[str]:
        """
        List of required data sources

        Possible sources:
        - predictions
        - h2h_history
        - h2h_details
        - standings
        - team1_stats / team2_stats
        - injuries
        - top_scorers
        - top_assists
        - top_yellow / top_red
        """
        pass

    @abstractmethod
    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate indicators specific to this bet type

        Args:
            raw_data: Raw data collected from API

        Returns:
            Dictionary of calculated indicators
        """
        pass

    def analyze(self, raw_data: Dict[str, Any]) -> BetAnalysisData:
        """
        Main analysis method

        Args:
            raw_data: Raw data from API collection

        Returns:
            BetAnalysisData with indicators and metadata
        """
        logger.debug(f"Analyzing {self.bet_type}")

        # Calculate indicators
        indicators = self.calculate_indicators(raw_data)

        # Determine available sources
        sources_used = self._get_available_sources(raw_data)

        # Check coverage
        coverage_complete = self._check_coverage(sources_used)

        return BetAnalysisData(
            indicators=indicators,
            data_sources=sources_used,
            coverage_complete=coverage_complete
        )

    def _get_available_sources(self, raw_data: Dict[str, Any]) -> List[str]:
        """Identify which data sources are available"""
        sources = []

        if raw_data.get("predictions"):
            sources.append("predictions")
        if raw_data.get("h2h_history"):
            sources.append("h2h_history")
        if raw_data.get("h2h_details"):
            sources.append("h2h_details")
        if raw_data.get("standings"):
            sources.append("standings")
        if raw_data.get("team1_stats") or raw_data.get("team2_stats"):
            sources.append("team_statistics")
        if raw_data.get("injuries"):
            sources.append("injuries")
        if raw_data.get("top_scorers"):
            sources.append("top_scorers")
        if raw_data.get("top_assists"):
            sources.append("top_assists")
        if raw_data.get("top_yellow") or raw_data.get("top_red"):
            sources.append("top_cards")
        if (
            raw_data.get("team1_recent_fixtures")
            or raw_data.get("team2_recent_fixtures")
            or raw_data.get("team1_recent_fixtures_league")
            or raw_data.get("team2_recent_fixtures_league")
        ):
            sources.append("recent_fixtures")
        if raw_data.get("recent_fixture_stats"):
            sources.append("recent_fixture_stats")

        return sources

    def _check_coverage(self, available_sources: List[str]) -> bool:
        """Check if all required sources are available"""
        for required in self.required_sources:
            if required not in available_sources:
                logger.warning(
                    f"[{self.bet_type}] Missing required source: {required}"
                )
                return False
        return True

    def _safe_get(self, data: Any, *keys, default=None):
        """Safely get nested dict value"""
        try:
            result = data
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key)
                else:
                    return default
                if result is None:
                    return default
            return result
        except (KeyError, TypeError, AttributeError):
            return default

    def _extract_team_matches(self, fixtures: List[Dict[str, Any]], team_id: int) -> List[Dict[str, Any]]:
        """Extract finished matches for a team with result and goals."""
        if not fixtures or not team_id:
            return []

        matches = []
        for fixture in fixtures:
            teams = fixture.get("teams") or {}
            home = teams.get("home") or {}
            away = teams.get("away") or {}
            home_id = home.get("id")
            away_id = away.get("id")

            if team_id not in (home_id, away_id):
                continue

            goals = fixture.get("goals") or {}
            home_goals = goals.get("home")
            away_goals = goals.get("away")
            if home_goals is None or away_goals is None:
                continue

            status = self._safe_get(fixture, "fixture", "status", "short")
            if status and status not in ["FT", "AET", "PEN"]:
                continue

            is_home = team_id == home_id
            goals_for = home_goals if is_home else away_goals
            goals_against = away_goals if is_home else home_goals

            if goals_for > goals_against:
                result = "W"
            elif goals_for == goals_against:
                result = "D"
            else:
                result = "L"

            timestamp = self._safe_get(fixture, "fixture", "timestamp")
            if timestamp is None:
                date_str = self._safe_get(fixture, "fixture", "date")
                if date_str:
                    try:
                        timestamp = int(datetime.fromisoformat(date_str).timestamp())
                    except (TypeError, ValueError):
                        timestamp = 0
                else:
                    timestamp = 0

            matches.append({
                "fixture_id": self._safe_get(fixture, "fixture", "id"),
                "timestamp": timestamp,
                "result": result,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "home_away": "home" if is_home else "away",
                "league_id": self._safe_get(fixture, "league", "id")
            })

        matches.sort(key=lambda m: m.get("timestamp") or 0, reverse=True)
        return matches

    def _current_streak(self, sequence: List[Any]) -> Dict[str, Any]:
        """Return current streak value and length from a sequence."""
        if not sequence:
            return {"value": None, "length": 0}

        first = sequence[0]
        length = 0
        for item in sequence:
            if item == first:
                length += 1
            else:
                break

        return {"value": first, "length": length}

    def _summarize_result_sequence(self, sequence: List[str]) -> Dict[str, Any]:
        """Summarize a W/D/L sequence."""
        if not sequence:
            return {
                "matches": 0,
                "sequence": "",
                "current_streak": {"value": None, "length": 0},
                "wins": 0,
                "draws": 0,
                "losses": 0
            }

        return {
            "matches": len(sequence),
            "sequence": "".join(sequence),
            "current_streak": self._current_streak(sequence),
            "wins": sequence.count("W"),
            "draws": sequence.count("D"),
            "losses": sequence.count("L")
        }

    def _summarize_boolean_sequence(self, sequence: List[bool]) -> Dict[str, Any]:
        """Summarize a boolean sequence with streaks and counts."""
        if not sequence:
            return {"matches": 0, "true": 0, "false": 0, "current_streak": {"value": None, "length": 0}}

        true_count = sum(1 for value in sequence if value)
        return {
            "matches": len(sequence),
            "true": true_count,
            "false": len(sequence) - true_count,
            "current_streak": self._current_streak(sequence)
        }
