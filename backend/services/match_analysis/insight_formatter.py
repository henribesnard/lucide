"""
Formateur d'insights pour l'analyse de match.
Implemente l'Etape 7 de l'algorithme.
"""

import logging
from typing import List
from .types import Pattern, HiddenAsset, NormalizedIDs

logger = logging.getLogger(__name__)


class InsightFormatter:
    """
    Formate les patterns en insights textuels.

    Etape 7: Restituer l'insight
    """

    def __init__(self):
        pass

    def format_insights(
        self,
        patterns: List[Pattern],
        normalized: NormalizedIDs,
    ) -> List[HiddenAsset]:
        """
        Etape 7: Formate chaque pattern en insight textuel.

        Returns:
            Liste de HiddenAssets avec textes formates
        """
        logger.info("=== ETAPE 7: Formatage des insights ===")

        hidden_assets = []

        for pattern in patterns:
            insight_text = self._generate_insight_text(pattern, normalized)
            confidence_level = self._determine_confidence_level(pattern)
            category = self._determine_category(pattern)

            hidden_asset = HiddenAsset(
                pattern=pattern,
                insight_text=insight_text,
                confidence_level=confidence_level,
                category=category,
                metadata={
                    "sample_size": pattern.matches,
                    "delta_baseline": pattern.delta_vs_baseline,
                    "confidence_score": pattern.confidence_score,
                },
            )
            hidden_assets.append(hidden_asset)

        logger.info(f"Formate {len(hidden_assets)} insights")
        return hidden_assets

    def _generate_insight_text(
        self, pattern: Pattern, normalized: NormalizedIDs
    ) -> str:
        """Genere le texte de l'insight."""
        # Determiner le nom de l'equipe
        team_name = (
            normalized.team_a_name
            if pattern.team == "team_a"
            else normalized.team_b_name
        )

        # Stats observees
        record = f"{pattern.wins}V-{pattern.draws}N-{pattern.loses}D"

        # Baseline comparison
        baseline_pct = pattern.baseline_win_rate
        delta = pattern.delta_vs_baseline

        # Construire le texte selon le type de pattern
        if pattern.pattern_type == "round":
            if pattern.is_extreme and pattern.win_rate == 0:
                text = (
                    f"{team_name} n'a jamais gagne {pattern.condition} "
                    f"({record}), alors que son taux de victoire global est {baseline_pct:.0f}%."
                )
            elif pattern.is_extreme and pattern.win_rate == 100:
                text = (
                    f"{team_name} gagne TOUJOURS {pattern.condition} "
                    f"({record}), contre {baseline_pct:.0f}% en moyenne."
                )
            elif pattern.is_strong:
                text = (
                    f"{team_name} gagne {pattern.win_rate:.0f}% des matchs {pattern.condition} "
                    f"({record}), contre {baseline_pct:.0f}% globalement."
                )
            else:
                text = (
                    f"{team_name} {pattern.condition}: {pattern.win_rate:.0f}% de victoires "
                    f"({record}), {delta:+.0f} pts vs baseline ({baseline_pct:.0f}%)."
                )

        elif pattern.pattern_type == "stadium":
            if pattern.is_extreme and pattern.win_rate == 0:
                text = (
                    f"{team_name} n'a jamais gagne {pattern.condition} "
                    f"({record}), alors que son taux de victoire global est {baseline_pct:.0f}%."
                )
            elif pattern.is_strong:
                text = (
                    f"{team_name} performe exceptionnellement {pattern.condition}: "
                    f"{pattern.win_rate:.0f}% de victoires ({record})."
                )
            else:
                text = (
                    f"{team_name} {pattern.condition}: {pattern.win_rate:.0f}% de victoires "
                    f"({record}), {delta:+.0f} pts vs baseline."
                )

        elif pattern.pattern_type == "formation":
            text = (
                f"{team_name} {pattern.condition}: {pattern.matches} matchs joues. "
                f"Performance a analyser en detail."
            )

        elif pattern.pattern_type == "streak":
            text = (
                f"{team_name} est actuellement {pattern.condition}, "
                f"sa meilleure serie recente."
            )

        elif pattern.pattern_type == "half_time":
            text = f"{team_name} {pattern.condition}."

        elif pattern.pattern_type in ["h2h", "h2h_stadium", "h2h_round"]:
            if pattern.is_extreme and pattern.win_rate == 0:
                text = (
                    f"{team_name} n'a jamais gagne {pattern.condition} "
                    f"({record})."
                )
            elif pattern.is_extreme and pattern.win_rate == 100:
                text = (
                    f"{team_name} gagne TOUJOURS {pattern.condition} "
                    f"({record})."
                )
            else:
                text = (
                    f"{team_name} {pattern.condition}: {pattern.win_rate:.0f}% de victoires "
                    f"({record})."
                )

        else:
            text = (
                f"{team_name} {pattern.condition}: {pattern.win_rate:.0f}% "
                f"({record})."
            )

        return text

    def _determine_confidence_level(self, pattern: Pattern) -> str:
        """Determine le niveau de confiance."""
        if pattern.confidence_score >= 0.7:
            return "high"
        elif pattern.confidence_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _determine_category(self, pattern: Pattern) -> str:
        """Determine la categorie de l'insight."""
        if pattern.is_extreme:
            return "rare"
        elif pattern.is_strong:
            return "strong"
        else:
            return "differential"
