"""
Assister Analyzer - Analyze assist providers
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetAssisterAnalyzer(BaseAnalyzer):
    """Analyzer for Assister bets"""

    @property
    def bet_type(self) -> str:
        return "assister"

    @property
    def required_sources(self) -> List[str]:
        return ["top_assists", "h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        top_assists = raw_data.get("top_assists") or []
        h2h_details = raw_data.get("h2h_details") or []
        fixture = raw_data.get("fixture") or {}

        home_team = self._safe_get(fixture, "teams", "home", "name")
        away_team = self._safe_get(fixture, "teams", "away", "name")

        return {
            "top_assisters_league": self._format_top_assisters(top_assists),
            "home_team_assisters": self._filter_assisters_by_team(top_assists, home_team),
            "away_team_assisters": self._filter_assisters_by_team(top_assists, away_team),
            "h2h_assisters": self._extract_h2h_assisters(h2h_details)
        }

    def _format_top_assisters(self, top_assists: list) -> list:
        """Format top assisters"""
        result = []

        for player_data in top_assists[:10]:
            player = player_data.get("player", {}) or {}
            stats = (player_data.get("statistics") or [{}])[0]
            goals = stats.get("goals", {}) or {}
            games = stats.get("games", {}) or {}

            # Try different keys for assists
            assists = (
                goals.get("assists") or
                stats.get("passes", {}).get("assists") or
                stats.get("passes", {}).get("total") or
                0
            )

            result.append({
                "name": player.get("name"),
                "team": self._safe_get(stats, "team", "name"),
                "assists": assists,
                "appearances": games.get("appearences", 0),
                "assists_per_90": self._calculate_assists_per_90(assists, games.get("minutes"))
            })

        return result

    def _filter_assisters_by_team(self, top_assists: list, team_name: str) -> list:
        """Filter assisters by team"""
        if not team_name:
            return []

        team_assisters = []

        for player_data in top_assists:
            stats = (player_data.get("statistics") or [{}])[0]
            player_team = self._safe_get(stats, "team", "name")

            if player_team and team_name.lower() in player_team.lower():
                player = player_data.get("player", {}) or {}
                goals = stats.get("goals", {}) or {}
                games = stats.get("games", {}) or {}

                assists = goals.get("assists") or stats.get("passes", {}).get("assists") or 0

                team_assisters.append({
                    "name": player.get("name"),
                    "assists": assists,
                    "assists_per_90": self._calculate_assists_per_90(assists, games.get("minutes"))
                })

        return team_assisters[:5]

    def _extract_h2h_assisters(self, h2h_details: list) -> dict:
        """Extract assisters from H2H matches"""
        assisters = {}

        for detail in h2h_details:
            events = detail.get("events") or []

            for event in events:
                if event.get("type") == "Goal":
                    assister_name = self._safe_get(event, "assist", "name")

                    if assister_name and assister_name != "None":
                        if assister_name not in assisters:
                            assisters[assister_name] = 0
                        assisters[assister_name] += 1

        # Sort by assists
        sorted_assisters = sorted(assisters.items(), key=lambda x: x[1], reverse=True)

        return {
            "assisters": [{"name": name, "assists": count} for name, count in sorted_assisters[:10]]
        }

    def _calculate_assists_per_90(self, assists, minutes):
        """Calculate assists per 90 minutes"""
        if not assists or not minutes or minutes == 0:
            return None
        return round((assists / minutes) * 90, 2)
