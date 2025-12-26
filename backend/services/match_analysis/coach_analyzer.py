"""
Module d'analyse des coaches et de leurs confrontations.
Detecte les patterns lies aux coaches independamment des equipes.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class CoachAnalyzer:
    """Analyse les coaches et leurs confrontations."""

    def analyze_coach_h2h(
        self,
        coach_a_history: List[Dict[str, Any]],
        coach_b_history: List[Dict[str, Any]],
        coach_a_name: str,
        coach_b_name: str
    ) -> Dict[str, Any]:
        """
        Analyse les confrontations directes entre 2 coaches
        (independamment des equipes qu'ils entrainent).

        Args:
            coach_a_history: Historique des matchs du coach A
            coach_b_history: Historique des matchs du coach B
            coach_a_name: Nom du coach A
            coach_b_name: Nom du coach B

        Returns:
            Dict avec bilan des confrontations
        """
        if not coach_a_history or not coach_b_history:
            return {}

        # Construire DataFrames
        df_a = pd.DataFrame(coach_a_history)
        df_b = pd.DataFrame(coach_b_history)

        if df_a.empty or df_b.empty:
            return {}

        # Trouver les matchs ou coach A a affronte coach B
        # (meme date, meme competition, equipes opposees)
        confrontations = []

        for _, match_a in df_a.iterrows():
            # Chercher dans l'historique de B un match le meme jour
            # ou B entraine l'equipe adverse
            match_b_candidates = df_b[
                (df_b["date"] == match_a["date"]) &
                (df_b["opponent_id"] == match_a["team_id"])
            ]

            if not match_b_candidates.empty:
                match_b = match_b_candidates.iloc[0]

                # Determiner le resultat pour coach A
                result_a = match_a["result"]

                confrontations.append({
                    "date": match_a["date"],
                    "coach_a_team": match_a["team"],
                    "coach_b_team": match_b["team"],
                    "score": f"{match_a['goals_for']}-{match_a['goals_against']}",
                    "result_coach_a": result_a,
                    "competition": match_a["competition"],
                })

        if not confrontations:
            return {}

        # Calculer stats
        conf_df = pd.DataFrame(confrontations)

        coach_a_wins = (conf_df["result_coach_a"] == "W").sum()
        draws = (conf_df["result_coach_a"] == "D").sum()
        coach_b_wins = (conf_df["result_coach_a"] == "L").sum()

        total = len(conf_df)
        coach_a_win_rate = coach_a_wins / total if total > 0 else 0

        return {
            "coach_a_name": coach_a_name,
            "coach_b_name": coach_b_name,
            "total_confrontations": total,
            "coach_a_wins": int(coach_a_wins),
            "draws": int(draws),
            "coach_b_wins": int(coach_b_wins),
            "coach_a_win_rate": float(coach_a_win_rate),
            "coach_b_win_rate": float(coach_b_wins / total) if total > 0 else 0,
            "confrontations": confrontations,
        }

    def analyze_coach_record(
        self,
        coach_history: List[Dict[str, Any]],
        coach_name: str
    ) -> Dict[str, Any]:
        """
        Analyse le bilan complet d'un coach (toutes equipes confondues).

        Args:
            coach_history: Historique des matchs du coach
            coach_name: Nom du coach

        Returns:
            Dict avec stats globales du coach
        """
        if not coach_history:
            return {}

        df = pd.DataFrame(coach_history)

        if df.empty:
            return {}

        total_matches = len(df)
        wins = (df["result"] == "W").sum()
        draws = (df["result"] == "D").sum()
        losses = (df["result"] == "L").sum()

        win_rate = wins / total_matches if total_matches > 0 else 0

        goals_for = df["goals_for"].sum()
        goals_against = df["goals_against"].sum()

        # Formations utilisees
        if "formation" in df.columns:
            formations = df["formation"].value_counts().to_dict()
        else:
            formations = {}

        # Bilan par competition
        if "competition" in df.columns:
            comp_records = {}
            for comp in df["competition"].unique():
                comp_df = df[df["competition"] == comp]
                comp_wins = (comp_df["result"] == "W").sum()
                comp_total = len(comp_df)
                comp_records[comp] = {
                    "matches": int(comp_total),
                    "wins": int(comp_wins),
                    "win_rate": float(comp_wins / comp_total) if comp_total > 0 else 0,
                }
        else:
            comp_records = {}

        return {
            "coach_name": coach_name,
            "total_matches": total_matches,
            "wins": int(wins),
            "draws": int(draws),
            "losses": int(losses),
            "win_rate": float(win_rate),
            "goals_for": int(goals_for),
            "goals_against": int(goals_against),
            "goals_per_match": float(goals_for / total_matches) if total_matches > 0 else 0,
            "formations": formations,
            "record_by_competition": comp_records,
        }

    def analyze_coach_with_current_team(
        self,
        coach_history: List[Dict[str, Any]],
        team_id: int,
        team_name: str,
        coach_name: str
    ) -> Dict[str, Any]:
        """
        Analyse le bilan du coach avec l'equipe actuelle uniquement.

        Args:
            coach_history: Historique complet du coach
            team_id: ID de l'equipe actuelle
            team_name: Nom de l'equipe actuelle
            coach_name: Nom du coach

        Returns:
            Dict avec stats du coach avec cette equipe
        """
        if not coach_history:
            return {}

        df = pd.DataFrame(coach_history)

        if df.empty or "team_id" not in df.columns:
            return {}

        # Filtrer sur l'equipe actuelle
        team_df = df[df["team_id"] == team_id]

        if team_df.empty:
            return {}

        total = len(team_df)
        wins = (team_df["result"] == "W").sum()
        draws = (team_df["result"] == "D").sum()
        losses = (team_df["result"] == "L").sum()

        win_rate = wins / total if total > 0 else 0

        return {
            "coach_name": coach_name,
            "team_name": team_name,
            "matches_with_team": total,
            "wins": int(wins),
            "draws": int(draws),
            "losses": int(losses),
            "win_rate": float(win_rate),
            "goals_for": int(team_df["goals_for"].sum()),
            "goals_against": int(team_df["goals_against"].sum()),
        }

    def compare_tactical_matchups(
        self,
        coach_a_history: List[Dict[str, Any]],
        coach_b_history: List[Dict[str, Any]],
        coach_a_name: str,
        coach_b_name: str
    ) -> Dict[str, Any]:
        """
        Compare les matchups tactiques entre 2 coaches.
        (Formations preferees et succes par formation)

        Returns:
            Dict avec formations preferees de chaque coach et leur efficacite
        """
        if not coach_a_history or not coach_b_history:
            return {}

        df_a = pd.DataFrame(coach_a_history)
        df_b = pd.DataFrame(coach_b_history)

        if df_a.empty or df_b.empty:
            return {}

        result = {
            "coach_a_name": coach_a_name,
            "coach_b_name": coach_b_name,
        }

        # Analyser formations coach A
        if "formation" in df_a.columns:
            formations_a = {}
            for formation in df_a["formation"].dropna().unique():
                form_df = df_a[df_a["formation"] == formation]
                wins = (form_df["result"] == "W").sum()
                total = len(form_df)

                formations_a[formation] = {
                    "matches": total,
                    "wins": int(wins),
                    "win_rate": float(wins / total) if total > 0 else 0,
                }

            result["coach_a_formations"] = formations_a

            # Formation preferee (la plus utilisee)
            most_used = df_a["formation"].value_counts().idxmax()
            result["coach_a_preferred_formation"] = most_used

        # Analyser formations coach B
        if "formation" in df_b.columns:
            formations_b = {}
            for formation in df_b["formation"].dropna().unique():
                form_df = df_b[df_b["formation"] == formation]
                wins = (form_df["result"] == "W").sum()
                total = len(form_df)

                formations_b[formation] = {
                    "matches": total,
                    "wins": int(wins),
                    "win_rate": float(wins / total) if total > 0 else 0,
                }

            result["coach_b_formations"] = formations_b

            most_used_b = df_b["formation"].value_counts().idxmax()
            result["coach_b_preferred_formation"] = most_used_b

        return result

    def analyze_coach_style(
        self,
        coach_history: List[Dict[str, Any]],
        coach_stats: List[Dict[str, Any]],
        coach_name: str
    ) -> Dict[str, Any]:
        """
        Analyse le style de jeu d'un coach (offensif, defensif, equilibre).

        Args:
            coach_history: Historique des matchs
            coach_stats: Stats detaillees des matchs
            coach_name: Nom du coach

        Returns:
            Dict avec style de jeu identifie
        """
        if not coach_history or not coach_stats:
            return {}

        df_history = pd.DataFrame(coach_history)
        df_stats = pd.DataFrame(coach_stats)

        if df_history.empty:
            return {}

        # Stats basiques
        goals_per_match = df_history["goals_for"].mean()
        goals_against_per_match = df_history["goals_against"].mean()
        clean_sheet_rate = (df_history["goals_against"] == 0).mean()

        result = {
            "coach_name": coach_name,
            "goals_per_match": float(goals_per_match),
            "goals_against_per_match": float(goals_against_per_match),
            "clean_sheet_rate": float(clean_sheet_rate),
        }

        # Si stats detaillees disponibles
        if not df_stats.empty and "possession" in df_stats.columns:
            avg_possession = df_stats["possession"].mean()
            result["avg_possession"] = float(avg_possession)

            # Classifier le style
            if avg_possession > 55 and goals_per_match > 1.5:
                style = "offensive_possession"
            elif avg_possession < 45 and clean_sheet_rate > 0.4:
                style = "defensive_counter"
            elif goals_per_match > 2.0:
                style = "offensive_direct"
            elif clean_sheet_rate > 0.5:
                style = "defensive_organized"
            else:
                style = "balanced"

            result["style"] = style

        return result
