"""
Causal rules engine for football match analysis.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .calculator import CausalCalculator


@dataclass
class CausalRule:
    rule_id: str
    category: str
    description: str
    cause: str
    mechanism: str
    confidence: str
    check: Callable[[Dict[str, object]], bool]


class CausalRuleEngine:
    """Evaluate predefined causal rules on a match data dict."""

    def __init__(self) -> None:
        self.rules = self._build_rules()

    def analyze(self, data: Dict[str, object]) -> List[Dict[str, object]]:
        findings: List[Dict[str, object]] = []
        for rule in self.rules:
            if rule.check(data):
                findings.append(
                    {
                        "rule_id": rule.rule_id,
                        "category": rule.category,
                        "cause": rule.cause,
                        "mechanism": rule.mechanism,
                        "confidence": rule.confidence,
                        "description": rule.description,
                    }
                )
        return findings

    def _build_rules(self) -> List[CausalRule]:
        return [
            CausalRule(
                rule_id="OFF_001",
                category="offense",
                description="xG much higher than goals scored",
                cause="finishing under-performance",
                mechanism="good chances not converted into goals",
                confidence="high",
                check=lambda d: _safe_float(d.get("xg_estime")) - _safe_float(d.get("goals")) >= 1.0,
            ),
            CausalRule(
                rule_id="OFF_002",
                category="offense",
                description="xG much lower than goals scored",
                cause="over-performance or luck",
                mechanism="goals exceed chance quality",
                confidence="high",
                check=lambda d: _safe_float(d.get("goals")) - _safe_float(d.get("xg_estime")) >= 1.0,
            ),
            CausalRule(
                rule_id="OFF_003",
                category="offense",
                description="high possession with low threat",
                cause="sterile possession",
                mechanism="ball control without penetration",
                confidence="medium",
                check=lambda d: _safe_float(d.get("possession")) >= 60
                and _safe_float(d.get("xg_estime")) < 1.0,
            ),
            CausalRule(
                rule_id="OFF_004",
                category="offense",
                description="low shot accuracy",
                cause="poor shot accuracy",
                mechanism="few shots on target",
                confidence="medium",
                check=lambda d: _shot_accuracy(d) is not None and _shot_accuracy(d) < 0.3,
            ),
            CausalRule(
                rule_id="DEF_001",
                category="defense",
                description="opponent shots on target high with goals conceded",
                cause="defensive pressure allowed",
                mechanism="opponent created high quality chances",
                confidence="medium",
                check=lambda d: _safe_float(d.get("shots_on_target_against")) >= 6
                and _safe_float(d.get("goals_conceded")) >= 2,
            ),
            CausalRule(
                rule_id="CTX_001",
                category="context",
                description="high fatigue score",
                cause="fatigue",
                mechanism="short rest reduces intensity",
                confidence="medium",
                check=lambda d: _safe_float(d.get("fatigue_score")) >= 0.7,
            ),
            CausalRule(
                rule_id="CTX_002",
                category="context",
                description="key absences detected",
                cause="key player absences",
                mechanism="reduced quality in key roles",
                confidence="medium",
                check=lambda d: _safe_float(d.get("key_absences")) >= 1,
            ),
            CausalRule(
                rule_id="CTX_003",
                category="context",
                description="match played on neutral ground",
                cause="neutral venue (no home advantage)",
                mechanism="international tournament or cup final - both teams play away from home",
                confidence="high",
                check=lambda d: d.get("is_neutral_venue") is True,
            ),
        ]


def _is_neutral_venue(fixture: Dict[str, object]) -> bool:
    """
    Detect if a match is played on neutral ground.
    Returns True for international tournaments (World Cup, continental championships)
    played outside the home countries of both teams.
    """
    league = fixture.get("league") or {}
    league_name = (league.get("name") or "").lower()
    venue = fixture.get("venue") or {}
    venue_country = venue.get("country")

    # International tournament keywords that typically use neutral venues
    neutral_tournaments = [
        "world cup",
        "africa cup",
        "african nations",
        "euro",
        "copa america",
        "asian cup",
        "concacaf",
        "nations league",
    ]

    # Check if it's an international tournament
    is_international = any(keyword in league_name for keyword in neutral_tournaments)
    if not is_international:
        return False

    # If it's a tournament and we have venue country info, check if it matches teams
    if venue_country:
        teams = fixture.get("teams") or {}
        home = teams.get("home") or fixture.get("home") or {}
        away = teams.get("away") or fixture.get("away") or {}
        home_name = (home.get("name") or "").lower()
        away_name = (away.get("name") or "").lower()
        venue_country_lower = venue_country.lower()

        # For national teams, the team name often matches the country
        # If neither team name matches the venue country, it's neutral
        home_matches_venue = venue_country_lower in home_name or home_name in venue_country_lower
        away_matches_venue = venue_country_lower in away_name or away_name in venue_country_lower

        if not home_matches_venue and not away_matches_venue:
            return True

    # For tournaments like "Africa Cup" or "World Cup", assume neutral venue
    # unless proven otherwise
    return is_international


def prepare_match_data_for_rules(
    fixture: Dict[str, object],
    statistics: List[Dict[str, object]],
    events: List[Dict[str, object]],
    team_id: Optional[int] = None,
    team_name: Optional[str] = None,
) -> Dict[str, object]:
    """
    Prepare match data for rules from summary tool outputs.
    """
    calculator = CausalCalculator()
    team_stats, opponent_stats, resolved = _select_team_stats(statistics, team_id, team_name)
    is_home = _infer_is_home(fixture, resolved)
    is_neutral = _is_neutral_venue(fixture)

    goals_for, goals_against = _extract_goals(fixture, resolved)
    result = _result_label(goals_for, goals_against)

    data = {
        "team_id": resolved.get("team_id"),
        "team_name": resolved.get("team_name"),
        "is_home": is_home,
        "is_neutral_venue": is_neutral,
        "goals": goals_for,
        "goals_conceded": goals_against,
        "result": result,
        "shots_total": _stat_value(team_stats, ["Total Shots"]),
        "shots_on_target": _stat_value(team_stats, ["Shots on Goal", "Shots on Target"]),
        "shots_inside_box": _stat_value(team_stats, ["Shots insidebox"]),
        "shots_outside_box": _stat_value(team_stats, ["Shots outsidebox"]),
        "possession": _stat_value(team_stats, ["Ball Possession"]),
        "corners": _stat_value(team_stats, ["Corner Kicks"]),
        "fouls": _stat_value(team_stats, ["Fouls"]),
        "passes_total": _stat_value(team_stats, ["Total passes"]),
        "passes_accuracy": _stat_value(team_stats, ["Passes %"]),
        "shots_total_against": _stat_value(opponent_stats, ["Total Shots"]),
        "shots_on_target_against": _stat_value(opponent_stats, ["Shots on Goal", "Shots on Target"]),
        "possession_against": _stat_value(opponent_stats, ["Ball Possession"]),
        "yellow_cards": _count_events(events, "Card", "Yellow"),
        "red_cards": _count_events(events, "Card", "Red"),
    }

    for key, value in list(data.items()):
        if isinstance(value, str) and value.endswith("%"):
            parsed = calculator.parse_stat_value(value)
            data[key] = parsed
    return data


def _safe_float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _shot_accuracy(data: Dict[str, object]) -> Optional[float]:
    shots_total = _safe_float(data.get("shots_total"))
    shots_on_target = _safe_float(data.get("shots_on_target"))
    if shots_total <= 0:
        return None
    return shots_on_target / shots_total


def _stat_value(stats_map: Dict[str, object], keys: List[str]) -> Optional[object]:
    if not stats_map:
        return None
    for key in keys:
        if key in stats_map:
            return stats_map.get(key)
    return None


def _select_team_stats(
    statistics: List[Dict[str, object]],
    team_id: Optional[int],
    team_name: Optional[str],
) -> Tuple[Dict[str, object], Dict[str, object], Dict[str, object]]:
    team_stats: Dict[str, object] = {}
    opponent_stats: Dict[str, object] = {}
    resolved = {"team_id": team_id, "team_name": team_name}

    if not statistics:
        return team_stats, opponent_stats, resolved

    def _match(stat: Dict[str, object]) -> bool:
        if team_id and stat.get("team_id") == team_id:
            return True
        if team_name and stat.get("team") and str(stat.get("team")).lower() == team_name.lower():
            return True
        return False

    if len(statistics) == 1:
        team_stats = statistics[0].get("stats") or {}
        resolved["team_id"] = statistics[0].get("team_id")
        resolved["team_name"] = statistics[0].get("team")
        return team_stats, opponent_stats, resolved

    matched = next((s for s in statistics if _match(s)), None)
    if matched:
        team_stats = matched.get("stats") or {}
        resolved["team_id"] = matched.get("team_id")
        resolved["team_name"] = matched.get("team")
        opponent = next((s for s in statistics if s is not matched), None)
        if opponent:
            opponent_stats = opponent.get("stats") or {}
        return team_stats, opponent_stats, resolved

    # fallback to first team
    team_stats = statistics[0].get("stats") or {}
    resolved["team_id"] = statistics[0].get("team_id")
    resolved["team_name"] = statistics[0].get("team")
    if len(statistics) > 1:
        opponent_stats = statistics[1].get("stats") or {}
    return team_stats, opponent_stats, resolved


def _infer_is_home(fixture: Dict[str, object], resolved: Dict[str, object]) -> Optional[bool]:
    teams = fixture.get("teams") if isinstance(fixture, dict) else {}
    if not teams:
        teams = {"home": fixture.get("home"), "away": fixture.get("away")}
    home = (teams or {}).get("home") or {}
    away = (teams or {}).get("away") or {}
    team_id = resolved.get("team_id")
    team_name = resolved.get("team_name")

    if team_id and home.get("id") == team_id:
        return True
    if team_id and away.get("id") == team_id:
        return False
    if team_name and home.get("name") and home.get("name").lower() == str(team_name).lower():
        return True
    if team_name and away.get("name") and away.get("name").lower() == str(team_name).lower():
        return False
    return None


def _extract_goals(fixture: Dict[str, object], resolved: Dict[str, object]) -> Tuple[int, int]:
    goals = (fixture or {}).get("goals") or {}
    teams = (fixture or {}).get("teams") or {}
    if not teams:
        teams = {"home": fixture.get("home"), "away": fixture.get("away")}
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    team_id = resolved.get("team_id")
    team_name = resolved.get("team_name")
    home_goals = int(goals.get("home") or (home.get("goals") or 0))
    away_goals = int(goals.get("away") or (away.get("goals") or 0))

    if team_id and home.get("id") == team_id:
        return home_goals, away_goals
    if team_id and away.get("id") == team_id:
        return away_goals, home_goals
    if team_name and home.get("name") and home.get("name").lower() == str(team_name).lower():
        return home_goals, away_goals
    if team_name and away.get("name") and away.get("name").lower() == str(team_name).lower():
        return away_goals, home_goals
    return home_goals, away_goals


def _result_label(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "win"
    if goals_for < goals_against:
        return "loss"
    return "draw"


def _count_events(events: List[Dict[str, object]], event_type: str, detail_fragment: str) -> int:
    count = 0
    for ev in events or []:
        if ev.get("type") == event_type and detail_fragment.lower() in str(ev.get("detail", "")).lower():
            count += 1
    return count
