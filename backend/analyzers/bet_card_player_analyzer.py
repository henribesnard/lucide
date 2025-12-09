"""
Card Player Analyzer - Analyze individual player cards
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetCardPlayerAnalyzer(BaseAnalyzer):
    """Analyzer for Player Card bets"""

    @property
    def bet_type(self) -> str:
        return "card_player"

    @property
    def required_sources(self) -> List[str]:
        return ["top_cards", "h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        top_yellow = raw_data.get("top_yellow") or []
        top_red = raw_data.get("top_red") or []

        return {
            "top_yellow_card_players": self._format_top_players(top_yellow, "yellow"),
            "top_red_card_players": self._format_top_players(top_red, "red"),
            "risk_players": self._identify_risk_players(top_yellow, top_red)
        }

    def _format_top_players(self, top_players: list, card_type: str) -> list:
        """Format top players with cards"""
        result = []

        for player_data in top_players[:10]:
            player = player_data.get("player", {}) or {}
            stats = (player_data.get("statistics") or [{}])[0]
            cards = stats.get("cards", {}) or {}

            card_count = cards.get(f"{card_type}") or cards.get(f"{card_type}cards", 0)

            result.append({
                "name": player.get("name"),
                "team": self._safe_get(stats, "team", "name"),
                "cards": card_count,
                "position": player.get("position") or self._safe_get(stats, "games", "position")
            })

        return result

    def _identify_risk_players(self, top_yellow: list, top_red: list) -> list:
        """Identify high-risk players"""
        risk_players = []

        # Players with many yellow cards
        for player_data in top_yellow[:5]:
            player = player_data.get("player", {}) or {}
            stats = (player_data.get("statistics") or [{}])[0]
            cards = stats.get("cards", {}) or {}

            yellow_count = cards.get("yellow") or cards.get("yellowcards", 0)

            if yellow_count and yellow_count >= 5:
                risk_players.append({
                    "name": player.get("name"),
                    "team": self._safe_get(stats, "team", "name"),
                    "yellow_cards": yellow_count,
                    "risk_level": "high" if yellow_count >= 8 else "medium"
                })

        return risk_players
