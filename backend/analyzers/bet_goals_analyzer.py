"""
Goals Analyzer - Analyze Over/Under bets
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class BetGoalsAnalyzer(BaseAnalyzer):
    """
    Analyzer for Goals bet (Over/Under)

    Indicators:
    - Average goals
    - Over 2.5%
    - BTTS (Both Teams To Score)
    - Clean sheets
    - H2H goals
    """

    @property
    def bet_type(self) -> str:
        return "goals"

    @property
    def required_sources(self) -> List[str]:
        return ["predictions", "h2h_history"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pred = raw_data.get("predictions") or {}
        h2h = raw_data.get("h2h_history") or []
        team1_stats = raw_data.get("team1_stats") or {}
        team2_stats = raw_data.get("team2_stats") or {}

        return {
            "average_goals": self._analyze_avg_goals(pred, team1_stats, team2_stats),
            "over_under": self._analyze_over_under(pred),
            "btts": self._analyze_btts(pred),
            "clean_sheets": self._analyze_clean_sheets(team1_stats, team2_stats),
            "h2h_goals": self._analyze_h2h_goals(h2h)
        }

    def _analyze_avg_goals(self, pred: dict, team1_stats: dict, team2_stats: dict) -> dict:
        """Analyze average goals"""
        teams = pred.get("teams", {}) or {}

        home_goals = self._safe_get(teams, "home", "league", "goals", "for", "average", "total")
        away_goals = self._safe_get(teams, "away", "league", "goals", "for", "average", "total")

        # From team statistics if available
        team1_avg_for = self._safe_get(team1_stats, "goals", "for", "average", "total")
        team2_avg_for = self._safe_get(team2_stats, "goals", "for", "average", "total")

        return {
            "home_avg_scored": home_goals or team1_avg_for,
            "away_avg_scored": away_goals or team2_avg_for,
            "combined_avg": self._safe_add(home_goals or team1_avg_for, away_goals or team2_avg_for)
        }

    def _analyze_over_under(self, pred: dict) -> dict:
        """Analyze Over/Under percentages"""
        goals = pred.get("goals", {}) or {}

        return {
            "over_0_5": self._safe_get(goals, "over_0_5"),
            "over_1_5": self._safe_get(goals, "over_1_5"),
            "over_2_5": self._safe_get(goals, "over_2_5"),
            "over_3_5": self._safe_get(goals, "over_3_5"),
            "under_0_5": self._safe_get(goals, "under_0_5"),
            "under_1_5": self._safe_get(goals, "under_1_5"),
            "under_2_5": self._safe_get(goals, "under_2_5"),
            "under_3_5": self._safe_get(goals, "under_3_5")
        }

    def _analyze_btts(self, pred: dict) -> dict:
        """Analyze Both Teams To Score"""
        teams = pred.get("teams", {}) or {}

        home_goals_for = self._safe_get(teams, "home", "league", "goals", "for", "total", "total")
        home_goals_against = self._safe_get(teams, "home", "league", "goals", "against", "total", "total")
        away_goals_for = self._safe_get(teams, "away", "league", "goals", "for", "total", "total")
        away_goals_against = self._safe_get(teams, "away", "league", "goals", "against", "total", "total")

        return {
            "home_scoring_frequency": home_goals_for,
            "home_conceding_frequency": home_goals_against,
            "away_scoring_frequency": away_goals_for,
            "away_conceding_frequency": away_goals_against,
            "btts_percentage": self._safe_get(pred, "goals", "btts")
        }

    def _analyze_clean_sheets(self, team1_stats: dict, team2_stats: dict) -> dict:
        """Analyze clean sheets"""
        return {
            "home_clean_sheets": self._safe_get(team1_stats, "clean_sheet", "total"),
            "away_clean_sheets": self._safe_get(team2_stats, "clean_sheet", "total")
        }

    def _analyze_h2h_goals(self, h2h: list) -> dict:
        """Analyze H2H goals"""
        if not h2h:
            return {"total_matches": 0}

        total_goals = 0
        over_2_5_count = 0

        goals_per_match = []

        for match in h2h:
            home_goals = self._safe_get(match, "goals", "home", default=0)
            away_goals = self._safe_get(match, "goals", "away", default=0)

            if home_goals is not None and away_goals is not None:
                match_total = home_goals + away_goals
                total_goals += match_total
                goals_per_match.append(match_total)

                if match_total > 2.5:
                    over_2_5_count += 1

        avg_goals = total_goals / len(h2h) if h2h else 0
        over_2_5_pct = (over_2_5_count / len(h2h) * 100) if h2h else 0

        return {
            "total_matches": len(h2h),
            "total_goals": total_goals,
            "avg_goals_per_match": round(avg_goals, 2),
            "over_2_5_count": over_2_5_count,
            "over_2_5_percentage": round(over_2_5_pct, 1),
            "goals_distribution": goals_per_match[:5]
        }

    def _safe_add(self, a, b):
        """Safely add two numbers (handle None)"""
        try:
            if a is None or b is None:
                return None
            return float(a) + float(b)
        except (TypeError, ValueError):
            return None
