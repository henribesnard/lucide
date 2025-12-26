"""
Feature Builder V2 - Version elargie avec analyses statistiques avancees.
Orchestre tous les analyseurs (statistical, events, players, coaches).
"""

import logging
from typing import Dict, List, Any
from .statistical_analyzer import DataFrameBuilder, StatisticalAnalyzer
from .events_analyzer import EventsAnalyzer
from .player_analyzer import PlayerAnalyzer
from .coach_analyzer import CoachAnalyzer

logger = logging.getLogger(__name__)


class FeatureBuilderV2:
    """
    Construit TOUTES les features avancees en orchestrant les analyseurs.
    """

    def __init__(self):
        self.df_builder = DataFrameBuilder()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.events_analyzer = EventsAnalyzer()
        self.player_analyzer = PlayerAnalyzer()
        self.coach_analyzer = CoachAnalyzer()

    def build_all_features(
        self,
        data: Dict[str, Any],
        normalized_ids: Any,
    ) -> Dict[str, Any]:
        """
        Construit TOUTES les features en une seule passe.

        Args:
            data: Donnees collectees (team_a_all_matches, events, stats, etc.)
            normalized_ids: IDs normalises

        Returns:
            Dict avec toutes les features:
            - dataframes: 4 DataFrames (matches, stats, events, lineups)
            - team_a_features: Features equipe A
            - team_b_features: Features equipe B
            - h2h_features: Features H2H
            - statistical_features: Analyses statistiques avancees
            - events_features: Analyses events/timeline
            - player_features: Analyses joueurs (impact, synergies)
            - coach_features: Analyses coaches (confrontations)
        """
        logger.info("=== CONSTRUCTION DES FEATURES (VERSION ELARGIE) ===")

        # 1) Construire les DataFrames
        logger.info("Construction des DataFrames...")

        matches_a_df = self.df_builder.build_matches_dataframe(
            data["team_a_all_matches"],
            normalized_ids.team_a_id,
            normalized_ids.team_a_name
        )

        matches_b_df = self.df_builder.build_matches_dataframe(
            data["team_b_all_matches"],
            normalized_ids.team_b_id,
            normalized_ids.team_b_name
        )

        stats_a_df = self.df_builder.build_stats_dataframe(
            data["stats_by_fixture"],
            normalized_ids.team_a_id
        )

        stats_b_df = self.df_builder.build_stats_dataframe(
            data["stats_by_fixture"],
            normalized_ids.team_b_id
        )

        events_a_df = self.df_builder.build_events_dataframe(
            data["events_by_fixture"],
            normalized_ids.team_a_id,
            normalized_ids.team_a_name
        )

        events_b_df = self.df_builder.build_events_dataframe(
            data["events_by_fixture"],
            normalized_ids.team_b_id,
            normalized_ids.team_b_name
        )

        lineups_a_df = self.df_builder.build_lineups_dataframe(
            data["lineups_by_fixture"],
            normalized_ids.team_a_id
        )

        lineups_b_df = self.df_builder.build_lineups_dataframe(
            data["lineups_by_fixture"],
            normalized_ids.team_b_id
        )

        # 2) Analyses statistiques
        logger.info("Analyses statistiques...")
        statistical_features_a = self._build_statistical_features(matches_a_df, stats_a_df)
        statistical_features_b = self._build_statistical_features(matches_b_df, stats_b_df)

        # 3) Analyses events
        logger.info("Analyses events/timeline...")
        events_features_a = self._build_events_features(matches_a_df, events_a_df)
        events_features_b = self._build_events_features(matches_b_df, events_b_df)

        # 4) Analyses joueurs
        logger.info("Analyses joueurs...")
        player_features_a = self._build_player_features(
            matches_a_df, lineups_a_df, events_a_df,
            data["injuries_team_a"], data["sidelined_team_a"]
        )
        player_features_b = self._build_player_features(
            matches_b_df, lineups_b_df, events_b_df,
            data["injuries_team_b"], data["sidelined_team_b"]
        )

        # 5) H2H
        h2h_matches_df = self.df_builder.build_matches_dataframe(
            data["h2h_matches"],
            normalized_ids.team_a_id,
            normalized_ids.team_a_name
        )

        logger.info("Construction features terminee")

        return {
            "dataframes": {
                "matches_a": matches_a_df,
                "matches_b": matches_b_df,
                "stats_a": stats_a_df,
                "stats_b": stats_b_df,
                "events_a": events_a_df,
                "events_b": events_b_df,
                "lineups_a": lineups_a_df,
                "lineups_b": lineups_b_df,
                "h2h": h2h_matches_df,
            },
            "team_a": {
                "statistical": statistical_features_a,
                "events": events_features_a,
                "players": player_features_a,
            },
            "team_b": {
                "statistical": statistical_features_b,
                "events": events_features_b,
                "players": player_features_b,
            },
            "h2h": {
                "total_matches": len(h2h_matches_df),
                "team_a_wins": int(h2h_matches_df["won"].sum()) if not h2h_matches_df.empty else 0,
            },
        }

    def _build_statistical_features(self, matches_df, stats_df):
        """Construit les features statistiques pour une equipe."""
        if matches_df.empty:
            return {}

        stat_columns = [
            "ball_possession", "total_shots", "shots_on_goal",
            "total_passes", "passes_accurate", "passes__pct"
        ]

        features = {
            "total_matches": len(matches_df),
            "wins": int(matches_df["won"].sum()),
            "win_rate": float(matches_df["won"].mean()),
            "goals_per_match": float(matches_df["goals_for"].mean()),
            "goals_against_per_match": float(matches_df["goals_against"].mean()),
            "clean_sheet_rate": float(matches_df["clean_sheet"].mean()),
        }

        # Stats descriptives
        if not stats_df.empty:
            features["descriptive_stats"] = self.statistical_analyzer.calculate_descriptive_stats(
                stats_df, stat_columns
            )

            # Correlations
            features["correlations"] = self.statistical_analyzer.calculate_correlations_with_wins(
                matches_df, stats_df, stat_columns
            )

        return features

    def _build_events_features(self, matches_df, events_df):
        """Construit les features events pour une equipe."""
        if matches_df.empty or events_df.empty:
            return {}

        features = {}

        # First goal impact
        features["first_goal"] = self.events_analyzer.analyze_first_goal_impact(
            matches_df, events_df
        )

        # Comeback ability
        features["comebacks"] = self.events_analyzer.analyze_comeback_ability(
            matches_df, events_df
        )

        # Early cards
        features["early_cards"] = self.events_analyzer.analyze_early_card_impact(
            matches_df, events_df, threshold_minute=30
        )

        # Goals heatmap
        features["goals_heatmap"] = self.events_analyzer.analyze_goals_heatmap(
            events_df, bins=[0, 15, 30, 45, 60, 75, 90, 120]
        )

        # Penalties
        features["penalties"] = self.events_analyzer.analyze_penalty_patterns(
            events_df
        )

        return features

    def _build_player_features(self, matches_df, lineups_df, events_df, injuries, sidelined):
        """Construit les features joueurs pour une equipe."""
        if lineups_df.empty:
            return {}

        features = {}

        # Identifier joueurs cles
        key_players = self.player_analyzer.identify_key_players(
            lineups_df, min_appearances=5
        )

        features["key_players"] = key_players

        # Impact des joueurs cles
        player_impacts = []
        for player in key_players[:5]:  # Top 5
            impact = self.player_analyzer.calculate_player_impact(
                matches_df, lineups_df,
                player["player_id"], player["player_name"]
            )
            if impact:
                player_impacts.append(impact)

        features["player_impacts"] = player_impacts

        # Synergies
        if len(key_players) >= 2:
            synergies = self.player_analyzer.detect_player_synergies(
                matches_df, lineups_df, key_players, min_matches_together=5
            )
            features["synergies"] = synergies

        # Disponibilite
        features["availability"] = self.player_analyzer.analyze_player_availability(
            injuries, sidelined, key_players
        )

        return features
