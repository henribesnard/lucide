"""
Corners Analyzer - Analyze corner kicks
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetCornersAnalyzer(BaseAnalyzer):
    """Analyzer for Corners bets"""

    @property
    def bet_type(self) -> str:
        return "corners"

    @property
    def required_sources(self) -> List[str]:
        return ["h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        h2h_details = raw_data.get("h2h_details") or []

        corners_data = self._extract_corners_from_h2h(h2h_details)

        return {
            "avg_corners": corners_data.get("avg_corners"),
            "over_9_5_pct": corners_data.get("over_9_5_pct"),
            "over_10_5_pct": corners_data.get("over_10_5_pct"),
            "h2h_stats": corners_data.get("h2h_stats", [])
        }

    def _extract_corners_from_h2h(self, h2h_details: list) -> dict:
        """Extract corner statistics from H2H details"""
        if not h2h_details:
            return {}

        total_corners = 0
        match_count = 0
        over_9_5 = 0
        over_10_5 = 0
        h2h_stats = []

        for detail in h2h_details:
            statistics = detail.get("statistics") or []

            match_corners = 0

            for team_stats in statistics:
                stats = team_stats.get("statistics") or []
                stats_map = {s.get("type"): s.get("value") for s in stats}

                corners = self._parse_int(stats_map.get("Corner Kicks"))

                if corners is not None:
                    match_corners += corners

            if match_corners > 0:
                total_corners += match_corners
                match_count += 1

                if match_corners > 9.5:
                    over_9_5 += 1
                if match_corners > 10.5:
                    over_10_5 += 1

                h2h_stats.append({
                    "fixture_id": detail.get("fixture_id"),
                    "total_corners": match_corners
                })

        avg_corners = total_corners / match_count if match_count > 0 else None
        over_9_5_pct = (over_9_5 / match_count * 100) if match_count > 0 else None
        over_10_5_pct = (over_10_5 / match_count * 100) if match_count > 0 else None

        return {
            "avg_corners": round(avg_corners, 1) if avg_corners else None,
            "over_9_5_pct": round(over_9_5_pct, 1) if over_9_5_pct else None,
            "over_10_5_pct": round(over_10_5_pct, 1) if over_10_5_pct else None,
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
