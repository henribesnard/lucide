"""
Module d'analyse statistique avancee avec pandas/numpy/scipy.
Construit les DataFrames et effectue les analyses statistiques.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from datetime import datetime

logger = logging.getLogger(__name__)


class DataFrameBuilder:
    """Construit les 4 DataFrames principaux a partir des donnees brutes."""

    def build_matches_dataframe(
        self,
        fixtures: List[Dict[str, Any]],
        team_id: int,
        team_name: str
    ) -> pd.DataFrame:
        """
        Construit le DataFrame des matchs.

        Args:
            fixtures: Liste des fixtures bruts de l'API
            team_id: ID de l'equipe analysee
            team_name: Nom de l'equipe analysee

        Returns:
            DataFrame avec colonnes: fixture_id, date, team, opponent,
            home_away, result, goals_for, goals_against, competition, etc.
        """
        rows = []

        for fixture in fixtures:
            # Determiner home/away et opponent
            home_team = fixture["teams"]["home"]
            away_team = fixture["teams"]["away"]

            if home_team["id"] == team_id:
                home_away = "home"
                opponent_id = away_team["id"]
                opponent_name = away_team["name"]
                goals_for = fixture["goals"]["home"]
                goals_against = fixture["goals"]["away"]
            else:
                home_away = "away"
                opponent_id = home_team["id"]
                opponent_name = home_team["name"]
                goals_for = fixture["goals"]["away"]
                goals_against = fixture["goals"]["home"]

            # Determiner le resultat (W/D/L)
            # Ignorer si pas de score (match annule ou a venir)
            if goals_for is None or goals_against is None:
                continue

            if goals_for > goals_against:
                result = "W"
            elif goals_for == goals_against:
                result = "D"
            else:
                result = "L"

            # Extraire infos match
            rows.append({
                "fixture_id": fixture["fixture"]["id"],
                "date": fixture["fixture"]["date"],
                "timestamp": fixture["fixture"]["timestamp"],
                "team": team_name,
                "team_id": team_id,
                "opponent": opponent_name,
                "opponent_id": opponent_id,
                "home_away": home_away,
                "result": result,
                "won": 1 if result == "W" else 0,
                "drew": 1 if result == "D" else 0,
                "lost": 1 if result == "L" else 0,
                "goals_for": goals_for if goals_for is not None else 0,
                "goals_against": goals_against if goals_against is not None else 0,
                "goal_difference": (goals_for or 0) - (goals_against or 0),
                "clean_sheet": 1 if goals_against == 0 else 0,
                "failed_to_score": 1 if goals_for == 0 else 0,
                "competition": fixture["league"]["name"],
                "competition_id": fixture["league"]["id"],
                "season": fixture["league"]["season"],
                "round": fixture["league"].get("round"),
                "status": fixture["fixture"]["status"]["short"],
            })

        df = pd.DataFrame(rows)

        # Convertir date en datetime
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            # Trier par date (plus recent en dernier)
            df = df.sort_values("date").reset_index(drop=True)

        return df

    def build_stats_dataframe(
        self,
        stats_by_fixture: Dict[int, Dict[str, Any]],
        team_id: int
    ) -> pd.DataFrame:
        """
        Construit le DataFrame des stats match par match.

        Args:
            stats_by_fixture: Dict {fixture_id: stats_data}
            team_id: ID de l'equipe

        Returns:
            DataFrame avec toutes les stats match (possession, shots, passes, etc.)
        """
        rows = []

        for fixture_id, stats_data in stats_by_fixture.items():
            if not stats_data:
                continue

            # stats_data est une liste de dicts (1 par equipe)
            team_stats = None
            for team_stat in stats_data:
                if team_stat.get("team", {}).get("id") == team_id:
                    team_stats = team_stat.get("statistics", [])
                    break

            if not team_stats:
                continue

            # Convertir liste de stats en dict
            stats_dict = {"fixture_id": fixture_id}
            for stat in team_stats:
                stat_type = stat.get("type")
                stat_value = stat.get("value")

                # Nettoyer le nom de stat pour etre une colonne valide
                col_name = stat_type.lower().replace(" ", "_").replace("%", "_pct")

                # Convertir en numerique si possible
                if stat_value is not None:
                    if isinstance(stat_value, str) and stat_value.endswith("%"):
                        stats_dict[col_name] = float(stat_value.rstrip("%"))
                    elif isinstance(stat_value, (int, float)):
                        stats_dict[col_name] = stat_value
                    else:
                        try:
                            stats_dict[col_name] = float(stat_value)
                        except (ValueError, TypeError):
                            stats_dict[col_name] = stat_value

            rows.append(stats_dict)

        df = pd.DataFrame(rows)
        return df

    def build_events_dataframe(
        self,
        events_by_fixture: Dict[int, List[Dict[str, Any]]],
        team_id: int,
        team_name: str
    ) -> pd.DataFrame:
        """
        Construit le DataFrame des events (timeline).

        Args:
            events_by_fixture: Dict {fixture_id: events_list}
            team_id: ID de l'equipe
            team_name: Nom de l'equipe

        Returns:
            DataFrame des events (buts, cartons, subst) avec timeline
        """
        rows = []

        for fixture_id, events in events_by_fixture.items():
            if not events:
                continue

            for event in events:
                minute = event.get("time", {}).get("elapsed", 0)
                extra_time = event.get("time", {}).get("extra")
                event_team_id = event.get("team", {}).get("id")
                event_team_name = event.get("team", {}).get("name")

                # Determiner si c'est notre equipe ou l'adversaire
                is_our_team = event_team_id == team_id

                rows.append({
                    "fixture_id": fixture_id,
                    "minute": minute,
                    "extra_time": extra_time,
                    "type": event.get("type"),
                    "detail": event.get("detail"),
                    "team_id": event_team_id,
                    "team_name": event_team_name,
                    "is_our_team": is_our_team,
                    "player_id": event.get("player", {}).get("id"),
                    "player_name": event.get("player", {}).get("name"),
                    "assist_id": event.get("assist", {}).get("id"),
                    "assist_name": event.get("assist", {}).get("name"),
                    "comments": event.get("comments"),
                })

        df = pd.DataFrame(rows)

        if not df.empty:
            # Trier par fixture puis minute
            df = df.sort_values(["fixture_id", "minute"]).reset_index(drop=True)

        return df

    def build_lineups_dataframe(
        self,
        lineups_by_fixture: Dict[int, List[Dict[str, Any]]],
        team_id: int
    ) -> pd.DataFrame:
        """
        Construit le DataFrame des lineups (joueur par joueur, match par match).

        Args:
            lineups_by_fixture: Dict {fixture_id: lineups_data}
            team_id: ID de l'equipe

        Returns:
            DataFrame des joueurs par match (position, starter, rating, stats)
        """
        rows = []

        for fixture_id, lineups_data in lineups_by_fixture.items():
            if not lineups_data:
                continue

            # lineups_data est une liste (1 par equipe)
            team_lineup = None
            for lineup in lineups_data:
                if lineup.get("team", {}).get("id") == team_id:
                    team_lineup = lineup
                    break

            if not team_lineup:
                continue

            formation = team_lineup.get("formation")
            startXI = team_lineup.get("startXI", [])
            substitutes = team_lineup.get("substitutes", [])

            # Traiter les titulaires
            for player_data in startXI:
                player = player_data.get("player", {})
                rows.append({
                    "fixture_id": fixture_id,
                    "team_id": team_id,
                    "formation": formation,
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "player_number": player.get("number"),
                    "position": player.get("pos"),
                    "grid": player.get("grid"),
                    "starter": True,
                })

            # Traiter les remplacants
            for player_data in substitutes:
                player = player_data.get("player", {})
                rows.append({
                    "fixture_id": fixture_id,
                    "team_id": team_id,
                    "formation": formation,
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "player_number": player.get("number"),
                    "position": player.get("pos"),
                    "grid": player.get("grid"),
                    "starter": False,
                })

        df = pd.DataFrame(rows)
        return df


class StatisticalAnalyzer:
    """Effectue les analyses statistiques avancees sur les DataFrames."""

    def __init__(self):
        self.df_builder = DataFrameBuilder()

    def calculate_competition_specific_stats(
        self,
        matches_df: pd.DataFrame,
        competition_id: int
    ) -> Dict[str, Any]:
        """
        Calcule des statistiques specifiques a une competition.

        Compare les performances dans la competition donnee vs toutes competitions.

        Args:
            matches_df: DataFrame des matchs (avec competition_id)
            competition_id: ID de la competition a analyser (ex: 6 pour CAN)

        Returns:
            Dict avec stats in_competition et stats global pour comparaison
        """
        if matches_df.empty:
            return {}

        # Filtrer matchs de la competition
        comp_matches = matches_df[matches_df["competition_id"] == competition_id]

        if comp_matches.empty:
            return {
                "has_competition_data": False,
                "competition_id": competition_id,
            }

        # Stats dans la competition
        in_comp_total = len(comp_matches)
        in_comp_wins = comp_matches["won"].sum()
        in_comp_draws = comp_matches["drew"].sum()
        in_comp_losses = comp_matches["lost"].sum()
        in_comp_goals_for = comp_matches["goals_for"].sum()
        in_comp_goals_against = comp_matches["goals_against"].sum()
        in_comp_clean_sheets = comp_matches["clean_sheet"].sum()

        # Stats globales (toutes competitions)
        global_total = len(matches_df)
        global_wins = matches_df["won"].sum()
        global_goals_for = matches_df["goals_for"].sum()
        global_goals_against = matches_df["goals_against"].sum()
        global_clean_sheets = matches_df["clean_sheet"].sum()

        return {
            "has_competition_data": True,
            "competition_id": competition_id,
            "in_competition": {
                "total_matches": int(in_comp_total),
                "wins": int(in_comp_wins),
                "draws": int(in_comp_draws),
                "losses": int(in_comp_losses),
                "win_rate": float(in_comp_wins / in_comp_total) if in_comp_total > 0 else 0,
                "goals_per_match": float(in_comp_goals_for / in_comp_total) if in_comp_total > 0 else 0,
                "goals_against_per_match": float(in_comp_goals_against / in_comp_total) if in_comp_total > 0 else 0,
                "clean_sheet_rate": float(in_comp_clean_sheets / in_comp_total) if in_comp_total > 0 else 0,
            },
            "global": {
                "total_matches": int(global_total),
                "wins": int(global_wins),
                "win_rate": float(global_wins / global_total) if global_total > 0 else 0,
                "goals_per_match": float(global_goals_for / global_total) if global_total > 0 else 0,
                "goals_against_per_match": float(global_goals_against / global_total) if global_total > 0 else 0,
                "clean_sheet_rate": float(global_clean_sheets / global_total) if global_total > 0 else 0,
            },
        }

    def calculate_competition_specific_stats_direct(
        self,
        league_matches_df: pd.DataFrame,
        all_matches_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calcule les statistiques specifiques a une competition en utilisant directement
        le DataFrame des matchs de la ligue (au lieu de filtrer).

        Args:
            league_matches_df: DataFrame contenant UNIQUEMENT les matchs de la ligue (toutes saisons)
            all_matches_df: DataFrame contenant tous les matchs (toutes competitions)

        Returns:
            Dict avec stats in_competition et stats global pour comparaison
        """
        if league_matches_df.empty:
            return {
                "has_competition_data": False,
            }

        # Stats dans la competition (utilise directement le DataFrame de ligue)
        in_comp_total = len(league_matches_df)
        in_comp_wins = league_matches_df["won"].sum()
        in_comp_draws = league_matches_df["drew"].sum()
        in_comp_losses = league_matches_df["lost"].sum()
        in_comp_goals_for = league_matches_df["goals_for"].sum()
        in_comp_goals_against = league_matches_df["goals_against"].sum()
        in_comp_clean_sheets = league_matches_df["clean_sheet"].sum()

        # Stats globales (toutes competitions)
        global_total = len(all_matches_df)
        global_wins = all_matches_df["won"].sum()
        global_goals_for = all_matches_df["goals_for"].sum()
        global_goals_against = all_matches_df["goals_against"].sum()
        global_clean_sheets = all_matches_df["clean_sheet"].sum()

        return {
            "has_competition_data": True,
            "in_competition": {
                "total_matches": int(in_comp_total),
                "wins": int(in_comp_wins),
                "draws": int(in_comp_draws),
                "losses": int(in_comp_losses),
                "win_rate": float(in_comp_wins / in_comp_total) if in_comp_total > 0 else 0,
                "goals_per_match": float(in_comp_goals_for / in_comp_total) if in_comp_total > 0 else 0,
                "goals_against_per_match": float(in_comp_goals_against / in_comp_total) if in_comp_total > 0 else 0,
                "clean_sheet_rate": float(in_comp_clean_sheets / in_comp_total) if in_comp_total > 0 else 0,
            },
            "global": {
                "total_matches": int(global_total),
                "wins": int(global_wins),
                "win_rate": float(global_wins / global_total) if global_total > 0 else 0,
                "goals_per_match": float(global_goals_for / global_total) if global_total > 0 else 0,
                "goals_against_per_match": float(global_goals_against / global_total) if global_total > 0 else 0,
                "clean_sheet_rate": float(global_clean_sheets / global_total) if global_total > 0 else 0,
            },
        }

    def calculate_descriptive_stats(
        self,
        stats_df: pd.DataFrame,
        columns: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcule les statistiques descriptives (moyenne, std, min, max, etc.).

        Args:
            stats_df: DataFrame des stats
            columns: Colonnes a analyser

        Returns:
            Dict {column: {mean, std, min, max, q25, q50, q75}}
        """
        result = {}

        for col in columns:
            if col not in stats_df.columns:
                continue

            values = stats_df[col].dropna()
            if values.empty:
                continue

            result[col] = {
                "mean": float(values.mean()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "q25": float(values.quantile(0.25)),
                "median": float(values.quantile(0.50)),
                "q75": float(values.quantile(0.75)),
                "count": len(values),
            }

        return result

    def calculate_correlations_with_wins(
        self,
        matches_df: pd.DataFrame,
        stats_df: pd.DataFrame,
        stat_columns: List[str]
    ) -> Dict[str, Tuple[float, float]]:
        """
        Calcule les correlations entre chaque stat et les victoires.

        Args:
            matches_df: DataFrame des matchs
            stats_df: DataFrame des stats
            stat_columns: Colonnes de stats a analyser

        Returns:
            Dict {stat_name: (correlation, p_value)}
        """
        # Merger matches et stats
        merged = matches_df.merge(stats_df, on="fixture_id", how="left")

        if merged.empty or "won" not in merged.columns:
            return {}

        correlations = {}

        for col in stat_columns:
            if col not in merged.columns:
                continue

            # Supprimer les NaN
            data = merged[[col, "won"]].dropna()
            if len(data) < 3:  # Besoin d'au moins 3 points
                continue

            try:
                # Calcul correlation de Pearson
                corr, p_value = scipy_stats.pearsonr(data[col], data["won"])
                correlations[col] = (float(corr), float(p_value))
            except Exception as e:
                logger.warning(f"Erreur correlation pour {col}: {e}")

        return correlations

    def analyze_event_timeline(
        self,
        events_df: pd.DataFrame,
        event_type: str,
        bins: List[int] = None
    ) -> pd.Series:
        """
        Analyse la distribution temporelle d'un type d'event.

        Args:
            events_df: DataFrame des events
            event_type: Type d'event (Goal, Card, etc.)
            bins: Bins pour grouper les minutes (ex: [0,15,30,45,60,75,90])

        Returns:
            Series avec la distribution par periode
        """
        if events_df.empty:
            return pd.Series()

        # Filtrer par type et equipe
        filtered = events_df[
            (events_df["type"] == event_type) &
            (events_df["is_our_team"] == True)
        ]

        if filtered.empty:
            return pd.Series()

        # Grouper par bins si fourni
        if bins:
            filtered_copy = filtered.copy()
            filtered_copy["period"] = pd.cut(
                filtered_copy["minute"],
                bins=bins,
                include_lowest=True
            )
            return filtered_copy["period"].value_counts().sort_index()
        else:
            return filtered["minute"].value_counts().sort_index()

    def calculate_win_rate_by_condition(
        self,
        matches_df: pd.DataFrame,
        stats_df: pd.DataFrame,
        stat_column: str,
        threshold: float,
        operator: str = ">"
    ) -> Dict[str, Any]:
        """
        Calcule le win rate quand une stat respecte une condition.

        Args:
            matches_df: DataFrame des matchs
            stats_df: DataFrame des stats
            stat_column: Colonne de stat a analyser
            threshold: Seuil
            operator: Operateur (">", ">=", "<", "<=", "==")

        Returns:
            Dict avec win_rate_when_true, win_rate_when_false, delta, sample_sizes
        """
        # Merger
        merged = matches_df.merge(stats_df, on="fixture_id", how="left")

        if stat_column not in merged.columns:
            return {}

        # Appliquer condition
        if operator == ">":
            condition = merged[stat_column] > threshold
        elif operator == ">=":
            condition = merged[stat_column] >= threshold
        elif operator == "<":
            condition = merged[stat_column] < threshold
        elif operator == "<=":
            condition = merged[stat_column] <= threshold
        elif operator == "==":
            condition = merged[stat_column] == threshold
        else:
            return {}

        # Calculer win rates
        when_true = merged[condition]
        when_false = merged[~condition]

        if when_true.empty or when_false.empty:
            return {}

        wr_true = when_true["won"].mean()
        wr_false = when_false["won"].mean()

        return {
            "win_rate_when_true": float(wr_true),
            "win_rate_when_false": float(wr_false),
            "delta": float(wr_true - wr_false),
            "sample_size_true": len(when_true),
            "sample_size_false": len(when_false),
            "wins_when_true": int(when_true["won"].sum()),
            "wins_when_false": int(when_false["won"].sum()),
        }

    def test_statistical_significance(
        self,
        matches_df: pd.DataFrame,
        stats_df: pd.DataFrame,
        stat_column: str
    ) -> Dict[str, float]:
        """
        Test si une stat est significativement differente entre victoires et defaites.

        Args:
            matches_df: DataFrame des matchs
            stats_df: DataFrame des stats
            stat_column: Colonne de stat a tester

        Returns:
            Dict avec t_statistic, p_value, mean_wins, mean_losses
        """
        # Merger
        merged = matches_df.merge(stats_df, on="fixture_id", how="left")

        if stat_column not in merged.columns:
            return {}

        # Separer victoires et defaites
        wins = merged[merged["result"] == "W"][stat_column].dropna()
        losses = merged[merged["result"] == "L"][stat_column].dropna()

        if wins.empty or losses.empty:
            return {}

        try:
            # T-test
            t_stat, p_value = scipy_stats.ttest_ind(wins, losses)

            return {
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "mean_wins": float(wins.mean()),
                "mean_losses": float(losses.mean()),
                "significant": p_value < 0.05,
            }
        except Exception as e:
            logger.warning(f"Erreur t-test pour {stat_column}: {e}")
            return {}
