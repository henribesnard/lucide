"""
Module d'analyse de l'impact des joueurs.
Detecte l'impact individuel, les synergies duo/trio, et les joueurs cles.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional, Set
import pandas as pd
import numpy as np
from itertools import combinations

logger = logging.getLogger(__name__)


class PlayerAnalyzer:
    """Analyse l'impact des joueurs et detecte les synergies."""

    def identify_key_players(
        self,
        lineups_df: pd.DataFrame,
        min_appearances: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Identifie les joueurs cles (les plus utilises).

        Args:
            lineups_df: DataFrame des lineups
            min_appearances: Nombre minimum d'apparitions pour etre considere

        Returns:
            Liste des joueurs cles avec stats
        """
        if lineups_df.empty:
            return []

        # Filtrer les titulaires
        starters = lineups_df[lineups_df["starter"] == True]

        if starters.empty:
            return []

        # Compter les apparitions par joueur
        player_counts = starters.groupby(["player_id", "player_name"]).size().reset_index(name="appearances")

        # Filtrer par min_appearances
        key_players = player_counts[player_counts["appearances"] >= min_appearances]

        # Trier par nombre d'apparitions
        key_players = key_players.sort_values("appearances", ascending=False)

        # Convertir en liste de dicts
        result = []
        for _, row in key_players.iterrows():
            result.append({
                "player_id": int(row["player_id"]),
                "player_name": row["player_name"],
                "appearances": int(row["appearances"]),
            })

        return result

    def calculate_player_impact(
        self,
        matches_df: pd.DataFrame,
        lineups_df: pd.DataFrame,
        player_id: int,
        player_name: str
    ) -> Dict[str, Any]:
        """
        Calcule l'impact d'un joueur (win rate avec vs sans lui).

        Args:
            matches_df: DataFrame des matchs
            lineups_df: DataFrame des lineups
            player_id: ID du joueur
            player_name: Nom du joueur

        Returns:
            Dict avec win_rate_with, win_rate_without, delta, sample_sizes
        """
        if lineups_df.empty or matches_df.empty:
            return {}

        # Trouver les matchs ou le joueur est titulaire
        player_matches = lineups_df[
            (lineups_df["player_id"] == player_id) &
            (lineups_df["starter"] == True)
        ]["fixture_id"].unique()

        # Separer matchs avec/sans joueur
        with_player = matches_df[matches_df["fixture_id"].isin(player_matches)]
        without_player = matches_df[~matches_df["fixture_id"].isin(player_matches)]

        if with_player.empty or without_player.empty:
            return {}

        # Calculer win rates
        wr_with = with_player["won"].mean()
        wr_without = without_player["won"].mean()

        # Calculer autres stats
        wins_with = int(with_player["won"].sum())
        wins_without = int(without_player["won"].sum())

        goals_with = with_player["goals_for"].sum()
        goals_against_with = with_player["goals_against"].sum()
        goals_without = without_player["goals_for"].sum()
        goals_against_without = without_player["goals_against"].sum()

        return {
            "player_id": player_id,
            "player_name": player_name,
            "matches_with": len(with_player),
            "matches_without": len(without_player),
            "wins_with": wins_with,
            "wins_without": wins_without,
            "win_rate_with": float(wr_with),
            "win_rate_without": float(wr_without),
            "delta": float(wr_with - wr_without),
            "goals_per_match_with": float(goals_with / len(with_player)),
            "goals_per_match_without": float(goals_without / len(without_player)) if len(without_player) > 0 else 0,
            "goals_against_per_match_with": float(goals_against_with / len(with_player)),
            "goals_against_per_match_without": float(goals_against_without / len(without_player)) if len(without_player) > 0 else 0,
        }

    def detect_player_synergies(
        self,
        matches_df: pd.DataFrame,
        lineups_df: pd.DataFrame,
        key_players: List[Dict[str, Any]],
        min_matches_together: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detecte les synergies entre duos de joueurs.

        Args:
            matches_df: DataFrame des matchs
            lineups_df: DataFrame des lineups
            key_players: Liste des joueurs cles
            min_matches_together: Minimum de matchs ensemble pour valider

        Returns:
            Liste des synergies detectees
        """
        if lineups_df.empty or matches_df.empty or len(key_players) < 2:
            return []

        synergies = []

        # Tester tous les duos de joueurs cles
        for player1, player2 in combinations(key_players, 2):
            player1_id = player1["player_id"]
            player2_id = player2["player_id"]

            # Matchs ou les 2 jouent ensemble (titulaires)
            p1_matches = set(lineups_df[
                (lineups_df["player_id"] == player1_id) &
                (lineups_df["starter"] == True)
            ]["fixture_id"])

            p2_matches = set(lineups_df[
                (lineups_df["player_id"] == player2_id) &
                (lineups_df["starter"] == True)
            ]["fixture_id"])

            together_matches = p1_matches & p2_matches
            separate_matches = (p1_matches | p2_matches) - together_matches

            if len(together_matches) < min_matches_together:
                continue

            # Calculer win rates
            together_df = matches_df[matches_df["fixture_id"].isin(together_matches)]
            separate_df = matches_df[matches_df["fixture_id"].isin(separate_matches)]

            if together_df.empty or separate_df.empty:
                continue

            wr_together = together_df["won"].mean()
            wr_separate = separate_df["won"].mean()

            delta = wr_together - wr_separate

            # Seuil de delta significatif
            if abs(delta) >= 0.15:  # +/- 15 points
                synergies.append({
                    "player1_id": player1_id,
                    "player1_name": player1["player_name"],
                    "player2_id": player2_id,
                    "player2_name": player2["player_name"],
                    "matches_together": len(together_matches),
                    "matches_separate": len(separate_matches),
                    "wins_together": int(together_df["won"].sum()),
                    "wins_separate": int(separate_df["won"].sum()),
                    "win_rate_together": float(wr_together),
                    "win_rate_separate": float(wr_separate),
                    "delta": float(delta),
                })

        # Trier par delta absolu (synergies les plus fortes)
        synergies.sort(key=lambda x: abs(x["delta"]), reverse=True)

        return synergies

    def detect_trio_synergies(
        self,
        matches_df: pd.DataFrame,
        lineups_df: pd.DataFrame,
        key_players: List[Dict[str, Any]],
        min_matches_together: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Detecte les synergies entre trios de joueurs.

        Args:
            matches_df: DataFrame des matchs
            lineups_df: DataFrame des lineups
            key_players: Liste des joueurs cles
            min_matches_together: Minimum de matchs ensemble

        Returns:
            Liste des synergies trio
        """
        if lineups_df.empty or matches_df.empty or len(key_players) < 3:
            return []

        synergies = []

        # Limiter au top 8 joueurs pour eviter explosion combinatoire
        top_players = key_players[:8]

        # Tester tous les trios
        for p1, p2, p3 in combinations(top_players, 3):
            p1_id, p2_id, p3_id = p1["player_id"], p2["player_id"], p3["player_id"]

            # Matchs ou les 3 jouent ensemble
            p1_matches = set(lineups_df[
                (lineups_df["player_id"] == p1_id) &
                (lineups_df["starter"] == True)
            ]["fixture_id"])

            p2_matches = set(lineups_df[
                (lineups_df["player_id"] == p2_id) &
                (lineups_df["starter"] == True)
            ]["fixture_id"])

            p3_matches = set(lineups_df[
                (lineups_df["player_id"] == p3_id) &
                (lineups_df["starter"] == True)
            ]["fixture_id"])

            together_matches = p1_matches & p2_matches & p3_matches
            separate_matches = (p1_matches | p2_matches | p3_matches) - together_matches

            if len(together_matches) < min_matches_together:
                continue

            # Win rates
            together_df = matches_df[matches_df["fixture_id"].isin(together_matches)]
            separate_df = matches_df[matches_df["fixture_id"].isin(separate_matches)]

            if together_df.empty or separate_df.empty:
                continue

            wr_together = together_df["won"].mean()
            wr_separate = separate_df["won"].mean()
            delta = wr_together - wr_separate

            # Seuil plus eleve pour trios (plus rare)
            if abs(delta) >= 0.20:  # +/- 20 points
                synergies.append({
                    "player1_id": p1_id,
                    "player1_name": p1["player_name"],
                    "player2_id": p2_id,
                    "player2_name": p2["player_name"],
                    "player3_id": p3_id,
                    "player3_name": p3["player_name"],
                    "matches_together": len(together_matches),
                    "matches_separate": len(separate_matches),
                    "wins_together": int(together_df["won"].sum()),
                    "wins_separate": int(separate_df["won"].sum()),
                    "win_rate_together": float(wr_together),
                    "win_rate_separate": float(wr_separate),
                    "delta": float(delta),
                })

        synergies.sort(key=lambda x: abs(x["delta"]), reverse=True)
        return synergies

    def analyze_player_availability(
        self,
        injuries: List[Dict[str, Any]],
        sidelined: List[Dict[str, Any]],
        key_players: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Analyse la disponibilite des joueurs cles.

        Args:
            injuries: Liste des blessures actuelles
            sidelined: Liste des suspensions
            key_players: Liste des joueurs cles

        Returns:
            Dict avec injured_key_players et suspended_key_players
        """
        key_player_ids = {p["player_id"] for p in key_players}

        injured_key = []
        suspended_key = []

        # Verifier blessures
        for injury in injuries:
            player_id = injury.get("player", {}).get("id")
            if player_id in key_player_ids:
                injured_key.append({
                    "player_id": player_id,
                    "player_name": injury.get("player", {}).get("name"),
                    "type": injury.get("player", {}).get("type"),
                    "reason": injury.get("player", {}).get("reason"),
                })

        # Verifier suspensions
        for side in sidelined:
            player_id = side.get("player", {}).get("id")
            if player_id in key_player_ids:
                suspended_key.append({
                    "player_id": player_id,
                    "player_name": side.get("player", {}).get("name"),
                    "type": side.get("type"),
                    "start": side.get("start"),
                    "end": side.get("end"),
                })

        return {
            "injured_key_players": injured_key,
            "suspended_key_players": suspended_key,
            "total_unavailable": len(injured_key) + len(suspended_key),
        }

    def get_player_performance_when_in_form(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame,
        lineups_df: pd.DataFrame,
        player_id: int,
        player_name: str,
        form_window: int = 3
    ) -> Dict[str, Any]:
        """
        Analyse la performance de l'equipe quand un joueur est en forme.
        (en forme = a marque sur les N derniers matchs)

        Args:
            form_window: Nombre de matchs pour definir "en forme"

        Returns:
            Dict avec win_rate quand joueur en forme vs pas en forme
        """
        if events_df.empty or matches_df.empty or lineups_df.empty:
            return {}

        # Trouver les matchs ou le joueur a marque
        player_goals = events_df[
            (events_df["player_id"] == player_id) &
            (events_df["type"] == "Goal") &
            (events_df["detail"].isin(["Normal Goal", "Penalty"]))
        ]

        if player_goals.empty:
            return {}

        # Determiner quand le joueur est "en forme"
        # (a marque dans les N derniers matchs)
        player_matches = lineups_df[
            (lineups_df["player_id"] == player_id) &
            (lineups_df["starter"] == True)
        ]["fixture_id"].unique()

        # Trier les matchs par date
        player_matches_sorted = matches_df[
            matches_df["fixture_id"].isin(player_matches)
        ].sort_values("date")

        # Pour chaque match, regarder si le joueur a marque dans les N precedents
        in_form_matches = []
        not_in_form_matches = []

        for idx, row in player_matches_sorted.iterrows():
            fixture_id = row["fixture_id"]

            # Regarder les N matchs precedents
            previous_matches = player_matches_sorted[
                player_matches_sorted["date"] < row["date"]
            ].tail(form_window)

            # Verifier si le joueur a marque dans ces matchs
            scored_in_previous = player_goals[
                player_goals["fixture_id"].isin(previous_matches["fixture_id"])
            ]

            if not scored_in_previous.empty:
                in_form_matches.append(fixture_id)
            else:
                not_in_form_matches.append(fixture_id)

        if not in_form_matches or not not_in_form_matches:
            return {}

        # Calculer win rates
        in_form_df = matches_df[matches_df["fixture_id"].isin(in_form_matches)]
        not_in_form_df = matches_df[matches_df["fixture_id"].isin(not_in_form_matches)]

        wr_in_form = in_form_df["won"].mean()
        wr_not_in_form = not_in_form_df["won"].mean()

        return {
            "player_id": player_id,
            "player_name": player_name,
            "form_window": form_window,
            "matches_in_form": len(in_form_matches),
            "matches_not_in_form": len(not_in_form_matches),
            "wins_in_form": int(in_form_df["won"].sum()),
            "wins_not_in_form": int(not_in_form_df["won"].sum()),
            "win_rate_in_form": float(wr_in_form),
            "win_rate_not_in_form": float(wr_not_in_form),
            "delta": float(wr_in_form - wr_not_in_form),
        }
