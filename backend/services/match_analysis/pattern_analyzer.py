"""
Generateur et scoreur de patterns.
Implemente les Etapes 4, 5 et 6 de l'algorithme.
"""

import logging
from typing import List
from .types import FeatureSet, Pattern, MatchAnalysisInput, NormalizedIDs

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Genere et score les patterns detectes.

    Etape 4: Generer des patterns candidats
    Etape 5: Mesurer la force des patterns
    Etape 6: Selectionner les "assets caches"
    """

    def __init__(
        self,
        min_sample_size: int = 6,
        min_delta_baseline: float = 20.0,
        extreme_threshold: float = 95.0,
        strong_threshold: float = 80.0,
    ):
        self.min_sample_size = min_sample_size
        self.min_delta_baseline = min_delta_baseline
        self.extreme_threshold = extreme_threshold
        self.strong_threshold = strong_threshold

    # ========================================================================
    # ETAPE 4: GENERER DES PATTERNS CANDIDATS
    # ========================================================================

    def generate_patterns(
        self,
        features: FeatureSet,
        input_data: MatchAnalysisInput,
        normalized: NormalizedIDs,
    ) -> List[Pattern]:
        """
        Etape 4: Genere tous les patterns candidats.

        Returns:
            Liste de patterns candidats
        """
        logger.info("=== ETAPE 4: Generation des patterns ===")

        patterns = []

        # Team A patterns
        patterns.extend(
            self._generate_team_patterns(
                features.team_a,
                features.team_a_context,
                "team_a",
                normalized.team_a_name,
                input_data,
            )
        )

        # Team B patterns
        patterns.extend(
            self._generate_team_patterns(
                features.team_b,
                features.team_b_context,
                "team_b",
                normalized.team_b_name,
                input_data,
            )
        )

        # H2H patterns
        patterns.extend(
            self._generate_h2h_patterns(
                features.h2h, normalized.team_a_name, normalized.team_b_name, input_data
            )
        )

        logger.info(f"Genere {len(patterns)} patterns candidats")
        return patterns

    def _generate_team_patterns(
        self,
        team_features,
        context_features,
        team_label: str,
        team_name: str,
        input_data: MatchAnalysisInput,
    ) -> List[Pattern]:
        """Genere les patterns pour une equipe."""
        patterns = []
        baseline_win_rate = team_features.win_rate
        baseline_matches = (
            team_features.wins + team_features.draws + team_features.loses
        )

        # Pattern: Round specifique
        if context_features.round_matches > 0:
            pattern = Pattern(
                pattern_type="round",
                condition=f"dans le round '{input_data.round}'",
                team=team_label,
                wins=context_features.round_wins,
                draws=context_features.round_draws,
                loses=context_features.round_loses,
                matches=context_features.round_matches,
                win_rate=context_features.round_win_rate * 100,
                baseline_win_rate=baseline_win_rate * 100,
                baseline_matches=baseline_matches,
            )
            patterns.append(pattern)

        # Pattern: Stadium specifique
        if context_features.stadium_matches > 0:
            pattern = Pattern(
                pattern_type="stadium",
                condition=f"au stade '{input_data.stadium}'",
                team=team_label,
                wins=context_features.stadium_wins,
                draws=context_features.stadium_draws,
                loses=context_features.stadium_loses,
                matches=context_features.stadium_matches,
                win_rate=context_features.stadium_win_rate * 100,
                baseline_win_rate=baseline_win_rate * 100,
                baseline_matches=baseline_matches,
            )
            patterns.append(pattern)

        # Pattern: Formation specifique
        for formation, formation_matches in team_features.formations.items():
            if formation_matches >= self.min_sample_size:
                # Calculer win rate pour cette formation (approximatif)
                # Note: necessite des donnees plus detaillees pour etre precis
                pattern = Pattern(
                    pattern_type="formation",
                    condition=f"en formation {formation}",
                    team=team_label,
                    wins=0,  # TODO: calculer avec donnees detaillees
                    draws=0,
                    loses=0,
                    matches=formation_matches,
                    win_rate=baseline_win_rate * 100,  # Approximation
                    baseline_win_rate=baseline_win_rate * 100,
                    baseline_matches=baseline_matches,
                )
                patterns.append(pattern)

        # Pattern: Serie en cours
        if team_features.current_win_streak >= 3:
            pattern = Pattern(
                pattern_type="streak",
                condition=f"sur une serie de {team_features.current_win_streak} victoires",
                team=team_label,
                wins=team_features.current_win_streak,
                draws=0,
                loses=0,
                matches=team_features.current_win_streak,
                win_rate=100.0,
                baseline_win_rate=baseline_win_rate * 100,
                baseline_matches=baseline_matches,
            )
            patterns.append(pattern)

        # Pattern: Mi-temps (si donnees disponibles)
        if team_features.goals_for_first_half + team_features.goals_for_second_half > 0:
            total_goals = (
                team_features.goals_for_first_half
                + team_features.goals_for_second_half
            )
            pct_2nd_half = (
                team_features.goals_for_second_half / total_goals * 100
                if total_goals > 0
                else 0
            )

            if pct_2nd_half >= 70 or pct_2nd_half <= 30:
                pattern = Pattern(
                    pattern_type="half_time",
                    condition=f"marque {pct_2nd_half:.0f}% de ses buts en 2nde mi-temps",
                    team=team_label,
                    wins=0,
                    draws=0,
                    loses=0,
                    matches=baseline_matches,
                    win_rate=baseline_win_rate * 100,
                    baseline_win_rate=baseline_win_rate * 100,
                    baseline_matches=baseline_matches,
                )
                patterns.append(pattern)

        return patterns

    def _generate_h2h_patterns(
        self,
        h2h_features,
        team_a_name: str,
        team_b_name: str,
        input_data: MatchAnalysisInput,
    ) -> List[Pattern]:
        """Genere les patterns H2H."""
        patterns = []

        if h2h_features.total_matches == 0:
            return patterns

        # H2H global
        pattern = Pattern(
            pattern_type="h2h",
            condition=f"contre {team_b_name} (H2H)",
            team="team_a",
            wins=h2h_features.team_a_wins,
            draws=h2h_features.draws,
            loses=h2h_features.team_b_wins,
            matches=h2h_features.total_matches,
            win_rate=h2h_features.team_a_win_rate * 100,
            baseline_win_rate=50.0,  # Baseline neutre
            baseline_matches=h2h_features.total_matches,
        )
        patterns.append(pattern)

        # H2H au stade
        if h2h_features.h2h_at_stadium_matches > 0:
            win_rate_stadium = (
                h2h_features.h2h_at_stadium_wins
                / h2h_features.h2h_at_stadium_matches
                * 100
            )
            pattern = Pattern(
                pattern_type="h2h_stadium",
                condition=f"contre {team_b_name} au stade '{input_data.stadium}'",
                team="team_a",
                wins=h2h_features.h2h_at_stadium_wins,
                draws=0,
                loses=0,
                matches=h2h_features.h2h_at_stadium_matches,
                win_rate=win_rate_stadium,
                baseline_win_rate=h2h_features.team_a_win_rate * 100,
                baseline_matches=h2h_features.total_matches,
            )
            patterns.append(pattern)

        # H2H dans le round
        if h2h_features.h2h_in_round_matches > 0:
            win_rate_round = (
                h2h_features.h2h_in_round_wins
                / h2h_features.h2h_in_round_matches
                * 100
            )
            pattern = Pattern(
                pattern_type="h2h_round",
                condition=f"contre {team_b_name} dans le round '{input_data.round}'",
                team="team_a",
                wins=h2h_features.h2h_in_round_wins,
                draws=0,
                loses=0,
                matches=h2h_features.h2h_in_round_matches,
                win_rate=win_rate_round,
                baseline_win_rate=h2h_features.team_a_win_rate * 100,
                baseline_matches=h2h_features.total_matches,
            )
            patterns.append(pattern)

        return patterns

    # ========================================================================
    # ETAPE 5: MESURER LA FORCE DES PATTERNS
    # ========================================================================

    def score_patterns(
        self, patterns: List[Pattern], scope: dict
    ) -> List[Pattern]:
        """
        Etape 5: Mesure la force de chaque pattern.

        Returns:
            Liste de patterns avec scores assignes
        """
        logger.info("=== ETAPE 5: Scoring des patterns ===")

        for pattern in patterns:
            # Delta vs baseline
            pattern.delta_vs_baseline = (
                pattern.win_rate - pattern.baseline_win_rate
            )

            # Sample size score (0-1)
            pattern.sample_size_score = min(1.0, pattern.matches / 20.0)

            # Recency score (simplifie, toujours 1.0 pour l'instant)
            pattern.recency_score = 1.0

            # Confidence score (moyenne ponderee)
            pattern.confidence_score = (
                0.4 * pattern.sample_size_score +
                0.3 * pattern.recency_score +
                0.3 * min(1.0, abs(pattern.delta_vs_baseline) / 50.0)
            )

        logger.info(f"Patterns scores assignes")
        return patterns

    # ========================================================================
    # ETAPE 6: SELECTIONNER LES "ASSETS CACHES"
    # ========================================================================

    def filter_hidden_assets(self, patterns: List[Pattern]) -> List[Pattern]:
        """
        Etape 6: Filtre pour garder uniquement les patterns rares et differenciants.

        Returns:
            Liste de patterns selectionnés comme assets caches
        """
        logger.info("=== ETAPE 6: Selection des assets caches ===")

        hidden_assets = []

        for pattern in patterns:
            # Filtrer par sample size
            if pattern.matches < self.min_sample_size:
                continue

            # Filtrer par delta vs baseline
            if abs(pattern.delta_vs_baseline) < self.min_delta_baseline:
                continue

            # Identifier les extremes (0% ou 100%)
            if pattern.win_rate <= (100 - self.extreme_threshold) or pattern.win_rate >= self.extreme_threshold:
                pattern.is_extreme = True
                hidden_assets.append(pattern)
                continue

            # Identifier les forts (>= 80%)
            if pattern.win_rate >= self.strong_threshold:
                pattern.is_strong = True
                hidden_assets.append(pattern)
                continue

            # Rupture forte vs baseline
            if abs(pattern.delta_vs_baseline) >= 30.0:
                hidden_assets.append(pattern)

        logger.info(
            f"Selectionne {len(hidden_assets)} assets caches sur {len(patterns)} patterns"
        )
        return hidden_assets
