"""
Causal metrics calculator.
Provides lightweight causal indicators without heavy frameworks.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    @classmethod
    def from_sample_size(cls, n: int) -> "Confidence":
        if n >= 15:
            return cls.HIGH
        if n >= 5:
            return cls.MEDIUM
        return cls.LOW


@dataclass
class CausalEstimate:
    name: str
    observed_effect: float
    adjusted_effect: Optional[float]
    confidence: Confidence
    sample_size: int
    confounders_controlled: List[str]
    interpretation: str

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "observed_effect": self.observed_effect,
            "adjusted_effect": self.adjusted_effect,
            "confidence": self.confidence.value,
            "sample_size": self.sample_size,
            "confounders_controlled": self.confounders_controlled,
            "interpretation": self.interpretation,
        }


class CausalCalculator:
    """Compute simplified causal metrics from match stats."""

    def parse_stat_value(self, value: object) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip().replace("%", "")
            try:
                return float(cleaned)
            except ValueError:
                return None
        return None

    def xg_estimate(self, stats_map: Dict[str, object]) -> float:
        """
        Estimate xG from basic shot distribution.
        Heuristic: inside box shots are higher value than outside.
        """
        shots_inside = self.parse_stat_value(stats_map.get("Shots insidebox"))
        shots_outside = self.parse_stat_value(stats_map.get("Shots outsidebox"))
        total_shots = self.parse_stat_value(stats_map.get("Total Shots"))

        if shots_inside is not None and shots_outside is not None:
            xg = shots_inside * 0.12 + shots_outside * 0.04
            return round(xg, 2)
        if total_shots is not None:
            return round(total_shots * 0.08, 2)
        return 0.0

    def xg_analysis(self, stats_map: Dict[str, object], actual_goals: int) -> Dict[str, object]:
        xg = self.xg_estimate(stats_map)
        delta = round(xg - float(actual_goals or 0), 2)
        interpretation = self._interpret_xg_delta(delta)
        cause_probable = self._xg_cause(delta)
        return {
            "xg_estime": xg,
            "buts_reels": actual_goals,
            "delta": delta,
            "interpretation": interpretation,
            "cause_probable": cause_probable,
        }

    def _interpret_xg_delta(self, delta: float) -> str:
        if delta >= 1.0:
            return "under-performance finishing"
        if delta <= -1.0:
            return "over-performance or luck"
        return "close to expected"

    def _xg_cause(self, delta: float) -> str:
        if delta >= 1.0:
            return "finishing issues or strong keeper"
        if delta <= -1.0:
            return "clinical finishing or luck"
        return "finishing aligned with chances"

    def fatigue_analysis(self, fixtures: List[Dict], reference_date: Optional[str] = None) -> Dict[str, object]:
        """
        Estimate fatigue from recent fixtures.
        fixtures: list of fixture summaries with 'date' fields.
        """
        if reference_date:
            ref = self._parse_date(reference_date) or datetime.utcnow()
        else:
            ref = datetime.utcnow()

        dates = []
        for fx in fixtures:
            date_str = fx.get("date")
            parsed = self._parse_date(date_str)
            if parsed:
                dates.append(parsed)

        matches_7 = sum(1 for d in dates if (ref - d).days <= 7)
        matches_14 = sum(1 for d in dates if (ref - d).days <= 14)
        days_rest = min([(ref - d).days for d in dates], default=None)

        fatigue_score = min(1.0, matches_7 * 0.3 + matches_14 * 0.1)
        impact = self._fatigue_impact(fatigue_score)

        return {
            "matches_7d": matches_7,
            "matches_14d": matches_14,
            "days_rest": days_rest,
            "fatigue_score": round(fatigue_score, 2),
            "impact_estime": impact,
        }

    def _fatigue_impact(self, score: float) -> str:
        if score >= 0.7:
            return "high fatigue impact"
        if score >= 0.4:
            return "medium fatigue impact"
        return "low fatigue impact"

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            if date_str.endswith("Z"):
                date_str = date_str.replace("Z", "+00:00")
            return datetime.fromisoformat(date_str)
        except Exception:
            return None
