"""
1X2 Analyzer - Analyze match result (Home win / Draw / Away win)
"""
from typing import Dict, Any, List
from backend.analyzers.base_analyzer import BaseAnalyzer


class Bet1X2Analyzer(BaseAnalyzer):
    """
    Analyzer for 1X2 bet (Match result)

    Indicators:
    - Recent form (W/D/L)
    - Home/Away performance
    - H2H history
    - Standings gap
    - API prediction
    """

    @property
    def bet_type(self) -> str:
        return "1x2"

    @property
    def required_sources(self) -> List[str]:
        return ["predictions", "h2h_history", "standings"]

    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        pred = raw_data.get("predictions") or {}
        h2h = raw_data.get("h2h_history") or []
        standings = raw_data.get("standings")
        fixture = raw_data.get("fixture") or {}

        home_id = self._safe_get(fixture, "teams", "home", "id")
        away_id = self._safe_get(fixture, "teams", "away", "id")

        return {
            "recent_form": self._analyze_form(pred),
            "h2h_stats": self._analyze_h2h(h2h, home_id, away_id),
            "standings_gap": self._analyze_standings(standings, home_id, away_id),
            "home_advantage": self._analyze_home_advantage(pred),
            "prediction_api": self._extract_prediction(pred)
        }

    def _analyze_form(self, pred: dict) -> dict:
        """Analyze recent form"""
        teams = pred.get("teams", {}) or {}

        home_team = teams.get("home", {}) or {}
        away_team = teams.get("away", {}) or {}

        home_league = home_team.get("league", {}) or {}
        away_league = away_team.get("league", {}) or {}

        return {
            "home": {
                "form": home_league.get("form"),
                "last_5_wins": self._count_wins_in_form(home_league.get("form")),
                "fixtures": home_league.get("fixtures", {})
            },
            "away": {
                "form": away_league.get("form"),
                "last_5_wins": self._count_wins_in_form(away_league.get("form")),
                "fixtures": away_league.get("fixtures", {})
            }
        }

    def _count_wins_in_form(self, form: str) -> int:
        """Count wins in form string (ex: WWDLW -> 3)"""
        if not form:
            return 0
        return form.count("W")

    def _analyze_h2h(self, h2h: list, home_id: int, away_id: int) -> dict:
        """Analyze head-to-head history"""
        if not h2h or not home_id or not away_id:
            return {"total": 0}

        home_wins = 0
        draws = 0
        away_wins = 0
        last_results = []

        for match in h2h:
            home_goals = self._safe_get(match, "goals", "home")
            away_goals = self._safe_get(match, "goals", "away")
            match_home_id = self._safe_get(match, "teams", "home", "id")

            if home_goals is None or away_goals is None:
                continue

            # Adjust based on who was home in the H2H match
            if match_home_id == home_id:
                if home_goals > away_goals:
                    home_wins += 1
                    result = "W"
                elif home_goals == away_goals:
                    draws += 1
                    result = "D"
                else:
                    away_wins += 1
                    result = "L"
            else:
                if away_goals > home_goals:
                    home_wins += 1
                    result = "W"
                elif home_goals == away_goals:
                    draws += 1
                    result = "D"
                else:
                    away_wins += 1
                    result = "L"

            last_results.append({
                "date": self._safe_get(match, "fixture", "date"),
                "result": result,
                "score": f"{home_goals}-{away_goals}"
            })

        return {
            "total": len(h2h),
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins,
            "last_5": last_results[:5]
        }

    def _analyze_standings(self, standings: Any, home_id: int, away_id: int) -> dict:
        """Analyze standings gap"""
        if not standings or not home_id or not away_id:
            return {}

        home_pos = None
        away_pos = None
        home_points = None
        away_points = None

        for block in (standings if isinstance(standings, list) else [standings]):
            table = self._safe_get(block, "league", "standings", default=[[]])[0]

            for entry in table:
                team_id = self._safe_get(entry, "team", "id")

                if team_id == home_id:
                    home_pos = entry.get("rank")
                    home_points = entry.get("points")
                elif team_id == away_id:
                    away_pos = entry.get("rank")
                    away_points = entry.get("points")

        if home_pos and away_pos:
            return {
                "home_position": home_pos,
                "away_position": away_pos,
                "position_gap": abs(home_pos - away_pos),
                "home_points": home_points,
                "away_points": away_points,
                "points_gap": (home_points - away_points) if home_points and away_points else None
            }

        return {}

    def _analyze_home_advantage(self, pred: dict) -> dict:
        """Analyze home advantage"""
        teams = pred.get("teams", {}) or {}

        home_fixtures = self._safe_get(teams, "home", "league", "fixtures", "wins", default={})
        away_fixtures = self._safe_get(teams, "away", "league", "fixtures", "wins", default={})

        return {
            "home_wins_at_home": self._safe_get(home_fixtures, "home"),
            "home_total_wins": self._safe_get(home_fixtures, "total"),
            "away_wins_away": self._safe_get(away_fixtures, "away"),
            "away_total_wins": self._safe_get(away_fixtures, "total")
        }

    def _extract_prediction(self, pred: dict) -> dict:
        """Extract API prediction"""
        predictions = pred.get("predictions", {}) or {}
        winner = predictions.get("winner", {}) or {}
        percent = predictions.get("percent", {}) or {}

        return {
            "winner": winner.get("name"),
            "winner_comment": winner.get("comment"),
            "win_percent": percent.get("home"),
            "draw_percent": percent.get("draw"),
            "lose_percent": percent.get("away"),
            "advice": predictions.get("advice")
        }
