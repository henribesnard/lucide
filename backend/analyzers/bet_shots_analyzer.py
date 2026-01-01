"""
Shots Analyzer - Analyze shots and shots on target
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetShotsAnalyzer(BaseAnalyzer):
    """Analyzer for Shots bets"""

    DEFAULT_SHOTS_THRESHOLD = 10
    DEFAULT_SHOTS_ON_TARGET_THRESHOLD = 4

    @property
    def bet_type(self) -> str:
        return "shots"

    @property
    def required_sources(self) -> List[str]:
        return ["h2h_details"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        h2h_details = raw_data.get("h2h_details") or []
        fixture = raw_data.get("fixture") or {}
        recent_limit = raw_data.get("recent_fixtures_last_n")

        shots_data = self._extract_shots_from_h2h(h2h_details)

        home_id = self._safe_get(fixture, "teams", "home", "id")
        away_id = self._safe_get(fixture, "teams", "away", "id")

        return {
            "avg_shots": shots_data.get("avg_shots"),
            "avg_shots_on_target": shots_data.get("avg_shots_on_target"),
            "accuracy_rate": shots_data.get("accuracy_rate"),
            "h2h_stats": shots_data.get("h2h_stats", []),
            "shots_series": self._analyze_shots_series(
                raw_data,
                home_id,
                away_id,
                recent_limit
            )
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

    def _analyze_shots_series(
        self,
        raw_data: Dict[str, Any],
        home_id: int,
        away_id: int,
        recent_limit: int
    ) -> dict:
        """Analyze shots streaks from recent fixture statistics."""
        if not home_id or not away_id:
            return {}

        limit = recent_limit or 5
        stats_by_fixture = raw_data.get("recent_fixture_stats") or {}

        team1_recent = raw_data.get("team1_recent_fixtures") or []
        team2_recent = raw_data.get("team2_recent_fixtures") or []
        team1_recent_league = raw_data.get("team1_recent_fixtures_league") or []
        team2_recent_league = raw_data.get("team2_recent_fixtures_league") or []

        return {
            "home": {
                "all_competitions": self._build_shots_series_bundle(
                    team1_recent, home_id, stats_by_fixture, limit
                ),
                "league": self._build_shots_series_bundle(
                    team1_recent_league, home_id, stats_by_fixture, limit
                )
            },
            "away": {
                "all_competitions": self._build_shots_series_bundle(
                    team2_recent, away_id, stats_by_fixture, limit
                ),
                "league": self._build_shots_series_bundle(
                    team2_recent_league, away_id, stats_by_fixture, limit
                )
            }
        }

    def _build_shots_series_bundle(
        self,
        fixtures: list,
        team_id: int,
        stats_by_fixture: Dict[str, Any],
        limit: int
    ) -> dict:
        """Build shots streaks for overall/home/away splits."""
        matches = self._extract_team_matches(fixtures, team_id)
        if not matches:
            return {}

        overall = matches[:limit]
        home_matches = [m for m in matches if m["home_away"] == "home"][:limit]
        away_matches = [m for m in matches if m["home_away"] == "away"][:limit]

        return {
            "overall": self._summarize_shots_series(overall, team_id, stats_by_fixture),
            "home": self._summarize_shots_series(home_matches, team_id, stats_by_fixture),
            "away": self._summarize_shots_series(away_matches, team_id, stats_by_fixture)
        }

    def _summarize_shots_series(
        self,
        matches: list,
        team_id: int,
        stats_by_fixture: Dict[str, Any]
    ) -> dict:
        """Summarize shots and shots on target streaks."""
        if not matches:
            return {}

        shots_values = []
        shots_on_target_values = []

        for match in matches:
            fixture_id = match.get("fixture_id")
            if not fixture_id:
                continue

            stats = stats_by_fixture.get(fixture_id)
            if not stats:
                continue

            team_stats = None
            for entry in stats:
                if (entry.get("team") or {}).get("id") == team_id:
                    team_stats = entry.get("statistics") or []
                    break

            if not team_stats:
                continue

            stats_map = {s.get("type"): s.get("value") for s in team_stats}
            shots = self._parse_int(stats_map.get("Total Shots"))
            shots_on_target = self._parse_int(
                stats_map.get("Shots on Goal") or stats_map.get("Shots on Target")
            )

            if shots is not None:
                shots_values.append(shots)
            if shots_on_target is not None:
                shots_on_target_values.append(shots_on_target)

        return {
            "shots": self._summarize_threshold_series(
                shots_values,
                self.DEFAULT_SHOTS_THRESHOLD
            ),
            "shots_on_target": self._summarize_threshold_series(
                shots_on_target_values,
                self.DEFAULT_SHOTS_ON_TARGET_THRESHOLD
            )
        }

    def _summarize_threshold_series(self, values: list, threshold: int) -> dict:
        """Summarize a threshold-based series for numeric values."""
        if not values:
            return {}

        over_count = sum(1 for value in values if value >= threshold)
        under_count = len(values) - over_count

        current_over = 0
        current_under = 0
        for value in values:
            if value >= threshold:
                current_over += 1
            else:
                break

        for value in values:
            if value < threshold:
                current_under += 1
            else:
                break

        avg_value = sum(values) / len(values) if values else 0

        return {
            "matches": len(values),
            "threshold": threshold,
            "over": over_count,
            "under": under_count,
            "current_over_streak": current_over,
            "current_under_streak": current_under,
            "average": round(avg_value, 1),
            "min": min(values),
            "max": max(values)
        }
