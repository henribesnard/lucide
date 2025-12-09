"""
Scorer Analyzer - Analyze goal scorers
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetScorerAnalyzer(BaseAnalyzer):
    """Analyzer for Scorer bets"""

    @property
    def bet_type(self) -> str:
        return "scorer"

    @property
    def required_sources(self) -> List[str]:
        return ["top_scorers", "h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        top_scorers = raw_data.get("top_scorers") or []
        h2h_details = raw_data.get("h2h_details") or []
        fixture = raw_data.get("fixture") or {}

        home_team = self._safe_get(fixture, "teams", "home", "name")
        away_team = self._safe_get(fixture, "teams", "away", "name")

        return {
            "top_scorers_league": self._format_top_scorers(top_scorers),
            "home_team_scorers": self._filter_scorers_by_team(top_scorers, home_team),
            "away_team_scorers": self._filter_scorers_by_team(top_scorers, away_team),
            "h2h_scorers": self._extract_h2h_scorers(h2h_details)
        }

    def _format_top_scorers(self, top_scorers: list) -> list:
        """Format top scorers"""
        result = []

        for player_data in top_scorers[:10]:
            player = player_data.get("player", {}) or {}
            stats = (player_data.get("statistics") or [{}])[0]
            goals = stats.get("goals", {}) or {}
            games = stats.get("games", {}) or {}

            result.append({
                "name": player.get("name"),
                "team": self._safe_get(stats, "team", "name"),
                "goals": goals.get("total", 0),
                "appearances": games.get("appearences", 0),
                "goals_per_90": self._calculate_goals_per_90(goals.get("total"), games.get("minutes"))
            })

        return result

    def _filter_scorers_by_team(self, top_scorers: list, team_name: str) -> list:
        """Filter scorers by team"""
        if not team_name:
            return []

        team_scorers = []

        for player_data in top_scorers:
            stats = (player_data.get("statistics") or [{}])[0]
            player_team = self._safe_get(stats, "team", "name")

            if player_team and team_name.lower() in player_team.lower():
                player = player_data.get("player", {}) or {}
                goals = stats.get("goals", {}) or {}
                games = stats.get("games", {}) or {}

                team_scorers.append({
                    "name": player.get("name"),
                    "goals": goals.get("total", 0),
                    "goals_per_90": self._calculate_goals_per_90(goals.get("total"), games.get("minutes"))
                })

        return team_scorers[:5]

    def _extract_h2h_scorers(self, h2h_details: list) -> dict:
        """Extract scorers from H2H matches"""
        scorers = {}

        for detail in h2h_details:
            events = detail.get("events") or []

            for event in events:
                if event.get("type") == "Goal":
                    player_name = self._safe_get(event, "player", "name")

                    if player_name:
                        if player_name not in scorers:
                            scorers[player_name] = 0
                        scorers[player_name] += 1

        # Sort by goals
        sorted_scorers = sorted(scorers.items(), key=lambda x: x[1], reverse=True)

        return {
            "scorers": [{"name": name, "goals": count} for name, count in sorted_scorers[:10]]
        }

    def _calculate_goals_per_90(self, goals, minutes):
        """Calculate goals per 90 minutes"""
        if not goals or not minutes or minutes == 0:
            return None
        return round((goals / minutes) * 90, 2)
