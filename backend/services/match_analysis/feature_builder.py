"""
Constructeur de features pour l'analyse de match.
Implemente l'Etape 3 de l'algorithme.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from .types import (
    FeatureSet,
    TeamFeatures,
    ContextFeatures,
    H2HFeatures,
    NormalizedIDs,
    MatchAnalysisInput,
)

logger = logging.getLogger(__name__)


class FeatureBuilder:
    """
    Construit les features a partir des donnees collectees.

    Etape 3: Construire les features (A, B, C, D)
    """

    def __init__(self):
        pass

    def build_features(
        self,
        data: Dict[str, Any],
        normalized: NormalizedIDs,
        input_data: MatchAnalysisInput,
    ) -> FeatureSet:
        """
        Etape 3: Construit toutes les features.

        Returns:
            FeatureSet complet
        """
        logger.info("=== ETAPE 3: Construction des features ===")

        # A) Features equipe
        team_a_features = self._build_team_features(
            data["team_a_fixtures"],
            data.get("team_a_statistics", {}),
            normalized.team_a_id,
        )
        team_b_features = self._build_team_features(
            data["team_b_fixtures"],
            data.get("team_b_statistics", {}),
            normalized.team_b_id,
        )

        # B) Features de contexte
        team_a_context = self._build_context_features(
            data["team_a_fixtures"],
            normalized.team_a_id,
            input_data.round,
            input_data.stadium,
            input_data.referee,
            normalized.coach_a_id,
        )
        team_b_context = self._build_context_features(
            data["team_b_fixtures"],
            normalized.team_b_id,
            input_data.round,
            input_data.stadium,
            input_data.referee,
            normalized.coach_b_id,
        )

        # C) Features joueurs / lineup - TODO si coverage disponible

        # D) Features H2H
        h2h_features = self._build_h2h_features(
            data["h2h_fixtures"],
            normalized.team_a_id,
            normalized.team_b_id,
            input_data.stadium,
            input_data.round,
        )

        # Baseline predictions
        baseline_predictions = data.get("predictions")

        features = FeatureSet(
            team_a=team_a_features,
            team_b=team_b_features,
            team_a_context=team_a_context,
            team_b_context=team_b_context,
            h2h=h2h_features,
            baseline_predictions=baseline_predictions,
        )

        logger.info("Features construites avec succes")
        return features

    # ========================================================================
    # A) FEATURES EQUIPE
    # ========================================================================

    def _build_team_features(
        self,
        fixtures: List[Dict[str, Any]],
        statistics: Dict[int, Dict[str, Any]],
        team_id: int,
    ) -> TeamFeatures:
        """Construit les features d'une equipe."""
        features = TeamFeatures()

        if not fixtures:
            return features

        # Forme globale
        wins, draws, loses = 0, 0, 0
        home_wins, home_draws, home_loses = 0, 0, 0
        away_wins, away_draws, away_loses = 0, 0, 0

        # Buts
        goals_for, goals_against = 0, 0
        goals_for_1h, goals_for_2h = 0, 0
        goals_against_1h, goals_against_2h = 0, 0

        # Buts par tranche
        goals_0_15, goals_16_30, goals_31_45 = 0, 0, 0
        goals_46_60, goals_61_75, goals_76_90 = 0, 0, 0

        clean_sheets, failed_to_score = 0, 0
        formations_counter = Counter()
        wins_by_formation = defaultdict(int)
        matches_by_formation = defaultdict(int)

        yellow_cards, red_cards = 0, 0
        yellow_76_90 = 0

        # Serie actuelle
        current_streak = []
        streaks = {"W": [], "D": [], "L": []}

        for fixture in fixtures:
            home_id = fixture["teams"]["home"]["id"]
            away_id = fixture["teams"]["away"]["id"]
            home_goals = fixture["goals"]["home"] or 0
            away_goals = fixture["goals"]["away"] or 0

            is_home = home_id == team_id
            team_goals = home_goals if is_home else away_goals
            opponent_goals = away_goals if is_home else home_goals

            # Resultat
            if team_goals > opponent_goals:
                result = "W"
                wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            elif team_goals < opponent_goals:
                result = "L"
                loses += 1
                if is_home:
                    home_loses += 1
                else:
                    away_loses += 1
            else:
                result = "D"
                draws += 1
                if is_home:
                    home_draws += 1
                else:
                    away_draws += 1

            # Streaks
            current_streak.append(result)
            if len(current_streak) > 1 and current_streak[-1] != current_streak[-2]:
                # Streak cassee
                if current_streak[-2] in streaks:
                    streaks[current_streak[-2]].append(len(current_streak) - 1)

            # Buts
            goals_for += team_goals
            goals_against += opponent_goals

            # Clean sheets / Failed to score
            if opponent_goals == 0:
                clean_sheets += 1
            if team_goals == 0:
                failed_to_score += 1

        # Calculs finaux
        total_matches = len(fixtures)
        features.wins = wins
        features.draws = draws
        features.loses = loses
        features.win_rate = wins / total_matches if total_matches > 0 else 0.0

        features.home_wins = home_wins
        features.home_draws = home_draws
        features.home_loses = home_loses
        features.away_wins = away_wins
        features.away_draws = away_draws
        features.away_loses = away_loses

        features.goals_for = goals_for
        features.goals_against = goals_against
        features.goals_for_first_half = goals_for_1h
        features.goals_for_second_half = goals_for_2h
        features.goals_against_first_half = goals_against_1h
        features.goals_against_second_half = goals_against_2h

        features.goals_for_0_15 = goals_0_15
        features.goals_for_16_30 = goals_16_30
        features.goals_for_31_45 = goals_31_45
        features.goals_for_46_60 = goals_46_60
        features.goals_for_61_75 = goals_61_75
        features.goals_for_76_90 = goals_76_90

        features.clean_sheets = clean_sheets
        features.failed_to_score = failed_to_score

        features.yellow_cards = yellow_cards
        features.red_cards = red_cards
        features.yellow_cards_76_90 = yellow_76_90

        # Streaks
        if current_streak:
            last_result = current_streak[-1]
            count = 1
            for i in range(len(current_streak) - 2, -1, -1):
                if current_streak[i] == last_result:
                    count += 1
                else:
                    break

            if last_result == "W":
                features.current_win_streak = count
            elif last_result == "D":
                features.current_draw_streak = count
            elif last_result == "L":
                features.current_lose_streak = count

        if streaks["W"]:
            features.biggest_win_streak = max(streaks["W"])

        # Stats de saison (depuis teams/statistics)
        if statistics:
            # Prendre la saison la plus recente
            latest_season = max(statistics.keys())
            season_stats = statistics[latest_season]

            if season_stats:
                # Formations
                lineups = season_stats.get("lineups", [])
                for lineup in lineups:
                    formation = lineup.get("formation", "")
                    played = lineup.get("played", 0)
                    features.formations[formation] = played

                # Penalties
                penalty_stats = season_stats.get("penalty", {})
                scored = penalty_stats.get("scored", {}).get("total", 0)
                missed = penalty_stats.get("missed", {}).get("total", 0)
                features.penalties_scored = scored
                features.penalties_missed = missed
                features.penalties_total = scored + missed
                if features.penalties_total > 0:
                    features.penalty_success_rate = scored / features.penalties_total

        return features

    # ========================================================================
    # B) FEATURES DE CONTEXTE
    # ========================================================================

    def _build_context_features(
        self,
        fixtures: List[Dict[str, Any]],
        team_id: int,
        round_filter: Optional[str],
        stadium_filter: Optional[str],
        referee_filter: Optional[str],
        coach_id: Optional[int],
    ) -> ContextFeatures:
        """Construit les features de contexte."""
        features = ContextFeatures()

        if not fixtures:
            return features

        # Filtrer par round
        if round_filter:
            round_matches = [
                f for f in fixtures if f.get("league", {}).get("round") == round_filter
            ]
            if round_matches:
                wins, draws, loses = self._count_results(round_matches, team_id)
                features.round_matches = len(round_matches)
                features.round_wins = wins
                features.round_draws = draws
                features.round_loses = loses
                features.round_win_rate = (
                    wins / features.round_matches if features.round_matches > 0 else 0.0
                )

        # Filtrer par stadium
        if stadium_filter:
            stadium_matches = [
                f
                for f in fixtures
                if stadium_filter.lower()
                in f.get("fixture", {}).get("venue", {}).get("name", "").lower()
            ]
            if stadium_matches:
                wins, draws, loses = self._count_results(stadium_matches, team_id)
                features.stadium_matches = len(stadium_matches)
                features.stadium_wins = wins
                features.stadium_draws = draws
                features.stadium_loses = loses
                features.stadium_win_rate = (
                    wins / features.stadium_matches
                    if features.stadium_matches > 0
                    else 0.0
                )

        # Stats referee - TODO: necessite d'aggreger tous les matchs arbitres par X

        # Stats coach - TODO: necessite historique coach

        return features

    def _count_results(
        self, fixtures: List[Dict[str, Any]], team_id: int
    ) -> tuple:
        """Compte W/D/L pour une liste de fixtures."""
        wins, draws, loses = 0, 0, 0

        for fixture in fixtures:
            home_id = fixture["teams"]["home"]["id"]
            away_id = fixture["teams"]["away"]["id"]
            home_goals = fixture["goals"]["home"] or 0
            away_goals = fixture["goals"]["away"] or 0

            is_home = home_id == team_id
            team_goals = home_goals if is_home else away_goals
            opponent_goals = away_goals if is_home else home_goals

            if team_goals > opponent_goals:
                wins += 1
            elif team_goals < opponent_goals:
                loses += 1
            else:
                draws += 1

        return wins, draws, loses

    # ========================================================================
    # D) FEATURES H2H
    # ========================================================================

    def _build_h2h_features(
        self,
        h2h_fixtures: List[Dict[str, Any]],
        team_a_id: int,
        team_b_id: int,
        stadium_filter: Optional[str],
        round_filter: Optional[str],
    ) -> H2HFeatures:
        """Construit les features H2H."""
        features = H2HFeatures()

        if not h2h_fixtures:
            return features

        features.total_matches = len(h2h_fixtures)

        # Compter wins team A vs team B
        team_a_wins, draws, team_b_wins = self._count_h2h_results(
            h2h_fixtures, team_a_id
        )
        features.team_a_wins = team_a_wins
        features.draws = draws
        features.team_b_wins = team_b_wins
        features.team_a_win_rate = (
            team_a_wins / features.total_matches if features.total_matches > 0 else 0.0
        )

        # H2H au stade
        if stadium_filter:
            stadium_h2h = [
                f
                for f in h2h_fixtures
                if stadium_filter.lower()
                in f.get("fixture", {}).get("venue", {}).get("name", "").lower()
            ]
            if stadium_h2h:
                features.h2h_at_stadium_matches = len(stadium_h2h)
                a_wins, _, _ = self._count_h2h_results(stadium_h2h, team_a_id)
                features.h2h_at_stadium_wins = a_wins

        # H2H dans le round
        if round_filter:
            round_h2h = [
                f
                for f in h2h_fixtures
                if f.get("league", {}).get("round") == round_filter
            ]
            if round_h2h:
                features.h2h_in_round_matches = len(round_h2h)
                a_wins, _, _ = self._count_h2h_results(round_h2h, team_a_id)
                features.h2h_in_round_wins = a_wins

        return features

    def _count_h2h_results(
        self, fixtures: List[Dict[str, Any]], team_a_id: int
    ) -> tuple:
        """Compte wins de team A dans les H2H."""
        team_a_wins, draws, team_b_wins = 0, 0, 0

        for fixture in fixtures:
            home_id = fixture["teams"]["home"]["id"]
            away_id = fixture["teams"]["away"]["id"]
            home_goals = fixture["goals"]["home"] or 0
            away_goals = fixture["goals"]["away"] or 0

            is_team_a_home = home_id == team_a_id
            team_a_goals = home_goals if is_team_a_home else away_goals
            team_b_goals = away_goals if is_team_a_home else home_goals

            if team_a_goals > team_b_goals:
                team_a_wins += 1
            elif team_a_goals < team_b_goals:
                team_b_wins += 1
            else:
                draws += 1

        return team_a_wins, draws, team_b_wins
