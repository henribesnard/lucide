"""
Shots Analyzer - Analyze shots and shots on target
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetShotsAnalyzer(BaseAnalyzer):
    """Analyzer for Shots bets"""

    @property
    def bet_type(self) -> str:
        return "shots"

    @property
    def required_sources(self) -> List[str]:
        return ["h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        h2h_details = raw_data.get("h2h_details") or []

        shots_data = self._extract_shots_from_h2h(h2h_details)

        return {
            "avg_shots": shots_data.get("avg_shots"),
            "avg_shots_on_target": shots_data.get("avg_shots_on_target"),
            "accuracy_rate": shots_data.get("accuracy_rate"),
            "h2h_stats": shots_data.get("h2h_stats", [])
        }

    def _extract_shots_from_h2h(self, h2h_details: list) -> dict:
        """Extract shots statistics from H2H details"""
        if not h2h_details:
            return {}

        total_shots = 0
        total_shots_on_target = 0
        match_count = 0
        h2h_stats = []

        for detail in h2h_details:
            statistics = detail.get("statistics") or []

            match_shots = 0
            match_shots_on_target = 0

            for team_stats in statistics:
                stats = team_stats.get("statistics") or []
                stats_map = {s.get("type"): s.get("value") for s in stats}

                shots = self._parse_int(stats_map.get("Total Shots"))
                shots_on_target = self._parse_int(stats_map.get("Shots on Goal"))

                if shots is not None:
                    match_shots += shots
                    total_shots += shots

                if shots_on_target is not None:
                    match_shots_on_target += shots_on_target
                    total_shots_on_target += shots_on_target

            if match_shots > 0:
                match_count += 1
                h2h_stats.append({
                    "fixture_id": detail.get("fixture_id"),
                    "total_shots": match_shots,
                    "shots_on_target": match_shots_on_target
                })

        avg_shots = total_shots / match_count if match_count > 0 else None
        avg_shots_on_target = total_shots_on_target / match_count if match_count > 0 else None
        accuracy = (total_shots_on_target / total_shots * 100) if total_shots > 0 else None

        return {
            "avg_shots": round(avg_shots, 1) if avg_shots else None,
            "avg_shots_on_target": round(avg_shots_on_target, 1) if avg_shots_on_target else None,
            "accuracy_rate": round(accuracy, 1) if accuracy else None,
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
