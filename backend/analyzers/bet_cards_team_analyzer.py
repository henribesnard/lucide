"""
Cards Team Analyzer - Analyze team cards
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetCardsTeamAnalyzer(BaseAnalyzer):
    """Analyzer for Team Cards bets"""

    @property
    def bet_type(self) -> str:
        return "cards_team"

    @property
    def required_sources(self) -> List[str]:
        return ["h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        h2h_details = raw_data.get("h2h_details") or []

        cards_data = self._extract_cards_from_h2h(h2h_details)

        return {
            "avg_yellow_cards": cards_data.get("avg_yellow"),
            "avg_red_cards": cards_data.get("avg_red"),
            "avg_total_cards": cards_data.get("avg_total"),
            "h2h_stats": cards_data.get("h2h_stats", [])
        }

    def _extract_cards_from_h2h(self, h2h_details: list) -> dict:
        """Extract cards statistics from H2H details"""
        if not h2h_details:
            return {}

        total_yellow = 0
        total_red = 0
        match_count = 0
        h2h_stats = []

        for detail in h2h_details:
            statistics = detail.get("statistics") or []

            match_yellow = 0
            match_red = 0

            for team_stats in statistics:
                stats = team_stats.get("statistics") or []
                stats_map = {s.get("type"): s.get("value") for s in stats}

                yellow = self._parse_int(stats_map.get("Yellow Cards"))
                red = self._parse_int(stats_map.get("Red Cards"))

                if yellow is not None:
                    match_yellow += yellow
                    total_yellow += yellow

                if red is not None:
                    match_red += red
                    total_red += red

            match_count += 1
            h2h_stats.append({
                "fixture_id": detail.get("fixture_id"),
                "yellow_cards": match_yellow,
                "red_cards": match_red,
                "total_cards": match_yellow + match_red
            })

        avg_yellow = total_yellow / match_count if match_count > 0 else None
        avg_red = total_red / match_count if match_count > 0 else None
        avg_total = (total_yellow + total_red) / match_count if match_count > 0 else None

        return {
            "avg_yellow": round(avg_yellow, 1) if avg_yellow else None,
            "avg_red": round(avg_red, 2) if avg_red else None,
            "avg_total": round(avg_total, 1) if avg_total else None,
            "h2h_stats": h2h_stats
        }

    def _parse_int(self, value):
        """Parse integer from various formats"""
        try:
            if value is None:
                return None
            return int(value)
        except (ValueError, TypeError):
            return None
