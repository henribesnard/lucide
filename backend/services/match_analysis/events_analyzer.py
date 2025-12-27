"""
Module d'analyse approfondie des events (timeline des matchs).
Detecte des patterns lies aux sequences d'events (buts, cartons, etc.).
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class EventsAnalyzer:
    """Analyse les patterns temporels et sequences d'events."""

    def analyze_first_goal_impact(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyse l'impact de marquer en premier vs encaisser en premier.

        Returns:
            Dict avec first_goal_rate, win_rate_when_score_first,
            win_rate_when_concede_first
        """
        if events_df.empty or matches_df.empty:
            return {}

        results = {
            "scored_first_count": 0,
            "conceded_first_count": 0,
            "wins_when_scored_first": 0,
            "wins_when_conceded_first": 0,
        }

        # Pour chaque match, trouver le premier but
        for fixture_id in matches_df["fixture_id"].unique():
            match_events = events_df[
                (events_df["fixture_id"] == fixture_id) &
                (events_df["type"] == "Goal") &
                (events_df["detail"].isin(["Normal Goal", "Penalty"]))
            ].sort_values("minute")

            if match_events.empty:
                continue

            # Premier but du match
            first_goal = match_events.iloc[0]
            scored_first = first_goal["is_our_team"]

            # Resultat du match
            match_result = matches_df[matches_df["fixture_id"] == fixture_id]["result"].values
            if len(match_result) == 0:
                continue

            result = match_result[0]

            if scored_first:
                results["scored_first_count"] += 1
                if result == "W":
                    results["wins_when_scored_first"] += 1
            else:
                results["conceded_first_count"] += 1
                if result == "W":
                    results["wins_when_conceded_first"] += 1

        # Calculer les rates
        total_with_goals = results["scored_first_count"] + results["conceded_first_count"]

        if total_with_goals == 0:
            return {}

        first_goal_rate = results["scored_first_count"] / total_with_goals

        win_rate_scored_first = (
            results["wins_when_scored_first"] / results["scored_first_count"]
            if results["scored_first_count"] > 0 else 0
        )

        win_rate_conceded_first = (
            results["wins_when_conceded_first"] / results["conceded_first_count"]
            if results["conceded_first_count"] > 0 else 0
        )

        return {
            "first_goal_rate": float(first_goal_rate),
            "scored_first_count": results["scored_first_count"],
            "conceded_first_count": results["conceded_first_count"],
            "win_rate_when_scored_first": float(win_rate_scored_first),
            "win_rate_when_conceded_first": float(win_rate_conceded_first),
            "wins_when_scored_first": results["wins_when_scored_first"],
            "wins_when_conceded_first": results["wins_when_conceded_first"],
            "delta": float(win_rate_scored_first - win_rate_conceded_first),
        }

    def analyze_comeback_ability(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyse la capacite a renverser des matchs apres avoir ete mene.

        Returns:
            Dict avec comeback_attempts, comeback_successes, comeback_rate
        """
        if events_df.empty or matches_df.empty:
            return {}

        comeback_attempts = 0
        comeback_successes = 0

        # Pour chaque match, verifier si l'equipe a ete menee puis a gagne
        for fixture_id in matches_df["fixture_id"].unique():
            match_events = events_df[
                (events_df["fixture_id"] == fixture_id) &
                (events_df["type"] == "Goal") &
                (events_df["detail"].isin(["Normal Goal", "Penalty", "Own Goal"]))
            ].sort_values("minute")

            if match_events.empty:
                continue

            # Calculer le score au fil du match
            score_us = 0
            score_them = 0
            was_behind = False

            for _, event in match_events.iterrows():
                if event["is_our_team"]:
                    if event["detail"] == "Own Goal":
                        score_them += 1
                    else:
                        score_us += 1
                else:
                    if event["detail"] == "Own Goal":
                        score_us += 1
                    else:
                        score_them += 1

                # Verifier si on est mene
                if score_us < score_them:
                    was_behind = True

            # Si on a ete mene, c'est une tentative de comeback
            if was_behind:
                comeback_attempts += 1

                # Verifier le resultat final
                match_result = matches_df[matches_df["fixture_id"] == fixture_id]["result"].values
                if len(match_result) > 0 and match_result[0] == "W":
                    comeback_successes += 1

        if comeback_attempts == 0:
            return {}

        comeback_rate = comeback_successes / comeback_attempts

        return {
            "comeback_attempts": comeback_attempts,
            "comeback_successes": comeback_successes,
            "comeback_failures": comeback_attempts - comeback_successes,
            "comeback_rate": float(comeback_rate),
        }

    def analyze_early_card_impact(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame,
        threshold_minute: int = 30
    ) -> Dict[str, Any]:
        """
        Analyse l'impact des cartons precoces (avant X minutes).

        Args:
            threshold_minute: Minute seuil (ex: 30 pour "avant 30 min")

        Returns:
            Dict avec win_rate avec/sans carton precoce
        """
        if events_df.empty or matches_df.empty:
            return {}

        with_early_card = []
        without_early_card = []

        for fixture_id in matches_df["fixture_id"].unique():
            match_events = events_df[
                (events_df["fixture_id"] == fixture_id) &
                (events_df["type"] == "Card") &
                (events_df["is_our_team"] == True)
            ]

            # Verifier si carton avant seuil
            early_cards = match_events[match_events["minute"] < threshold_minute]
            has_early_card = not early_cards.empty

            # Resultat du match
            match_result = matches_df[matches_df["fixture_id"] == fixture_id]["result"].values
            if len(match_result) == 0:
                continue

            result = match_result[0]

            if has_early_card:
                with_early_card.append(1 if result == "W" else 0)
            else:
                without_early_card.append(1 if result == "W" else 0)

        if not with_early_card or not without_early_card:
            return {}

        win_rate_with = np.mean(with_early_card)
        win_rate_without = np.mean(without_early_card)

        return {
            "win_rate_with_early_card": float(win_rate_with),
            "win_rate_without_early_card": float(win_rate_without),
            "delta": float(win_rate_with - win_rate_without),
            "sample_with_early_card": len(with_early_card),
            "sample_without_early_card": len(without_early_card),
            "wins_with_early_card": int(np.sum(with_early_card)),
            "wins_without_early_card": int(np.sum(without_early_card)),
            "threshold_minute": threshold_minute,
        }

    def analyze_goals_heatmap(
        self,
        events_df: pd.DataFrame,
        bins: List[int] = None
    ) -> Dict[str, Any]:
        """
        Analyse la distribution temporelle des buts (heatmap).

        Args:
            bins: Bins pour grouper les minutes (ex: [0,15,30,45,60,75,90])

        Returns:
            Dict avec distribution par periode et periode la plus prolifique
        """
        if events_df.empty:
            return {}

        if bins is None:
            bins = [0, 15, 30, 45, 60, 75, 90, 120]

        # Filtrer les buts de notre equipe
        goals = events_df[
            (events_df["type"] == "Goal") &
            (events_df["is_our_team"] == True) &
            (events_df["detail"].isin(["Normal Goal", "Penalty"]))
        ]

        if goals.empty:
            return {}

        # Grouper par bins
        goals_copy = goals.copy()
        goals_copy["period"] = pd.cut(
            goals_copy["minute"],
            bins=bins,
            include_lowest=True
        )

        distribution = goals_copy["period"].value_counts().sort_index()

        # Convertir en dict
        distribution_dict = {}
        total_goals = len(goals)

        for period, count in distribution.items():
            period_str = f"{int(period.left)}-{int(period.right)}min"
            distribution_dict[period_str] = {
                "count": int(count),
                "percentage": float(count / total_goals * 100),
            }

        # Trouver la periode la plus prolifique
        most_prolific_period = distribution.idxmax()
        most_prolific_count = distribution.max()

        return {
            "total_goals": total_goals,
            "distribution": distribution_dict,
            "most_prolific_period": f"{int(most_prolific_period.left)}-{int(most_prolific_period.right)}min",
            "most_prolific_count": int(most_prolific_count),
            "most_prolific_percentage": float(most_prolific_count / total_goals * 100),
        }

    def analyze_late_goals(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame,
        threshold_minute: int = 75
    ) -> Dict[str, Any]:
        """
        Analyse les buts tardifs (apres X minutes).

        Args:
            threshold_minute: Minute seuil (ex: 75 pour "apres 75 min")

        Returns:
            Dict avec late_goals_scored, late_goals_conceded, impact sur resultats
        """
        if events_df.empty or matches_df.empty:
            return {}

        late_goals_scored = 0
        late_goals_conceded = 0
        late_goals_changed_result = 0

        for fixture_id in matches_df["fixture_id"].unique():
            match_events = events_df[
                (events_df["fixture_id"] == fixture_id) &
                (events_df["type"] == "Goal") &
                (events_df["detail"].isin(["Normal Goal", "Penalty"]))
            ].sort_values("minute")

            if match_events.empty:
                continue

            # Score avant les buts tardifs
            score_us_before = 0
            score_them_before = 0

            for _, event in match_events.iterrows():
                if event["minute"] >= threshold_minute:
                    # But tardif
                    if event["is_our_team"]:
                        late_goals_scored += 1
                    else:
                        late_goals_conceded += 1

                    # Verifier si ca change le resultat
                    # (simplifie: comparer score avant vs apres)
                    if score_us_before == score_them_before:
                        # Match nul avant le but tardif
                        late_goals_changed_result += 1
                else:
                    # But avant seuil
                    if event["is_our_team"]:
                        score_us_before += 1
                    else:
                        score_them_before += 1

        total_late_goals = late_goals_scored + late_goals_conceded

        if total_late_goals == 0:
            return {}

        return {
            "late_goals_scored": late_goals_scored,
            "late_goals_conceded": late_goals_conceded,
            "total_late_goals": total_late_goals,
            "late_goals_scored_percentage": float(late_goals_scored / total_late_goals * 100),
            "late_goals_changed_result": late_goals_changed_result,
            "threshold_minute": threshold_minute,
        }

    def analyze_by_competition_phase(
        self,
        matches_df: pd.DataFrame,
        league_type: str
    ) -> Dict[str, Any]:
        """
        Analyse les performances par phase de compétition.

        Pour les COUPES: Group Stage - 1/2/3, Round of 16, Quarter-finals, etc.
        Pour les LEAGUES: Journée 1, Journée 10, Journée 38, ou début/milieu/fin

        Returns:
            Dict avec performances par phase
        """
        if matches_df.empty or "round" not in matches_df.columns:
            return {}

        phases_stats = {}

        # Pour chaque round unique
        for round_name in matches_df["round"].unique():
            if pd.isna(round_name):
                continue

            # Filtrer les matchs de cette phase
            phase_matches = matches_df[matches_df["round"] == round_name]

            total = len(phase_matches)
            wins = int(phase_matches["won"].sum())
            win_rate = wins / total if total > 0 else 0

            # Classifier la phase
            phase_category = self._classify_phase(round_name, league_type)

            if phase_category not in phases_stats:
                phases_stats[phase_category] = {
                    "total_matches": 0,
                    "wins": 0,
                    "rounds": []
                }

            phases_stats[phase_category]["total_matches"] += total
            phases_stats[phase_category]["wins"] += wins
            phases_stats[phase_category]["rounds"].append({
                "round_name": round_name,
                "matches": total,
                "wins": wins,
                "win_rate": float(win_rate)
            })

        # Calculer win_rate global par phase
        for phase, stats in phases_stats.items():
            stats["win_rate"] = stats["wins"] / stats["total_matches"] if stats["total_matches"] > 0 else 0

        return phases_stats

    def _classify_phase(self, round_name: str, league_type: str) -> str:
        """Classifie un round dans une catégorie de phase."""
        round_lower = round_name.lower()

        if league_type == "cup":
            # Phases de coupe
            if "group" in round_lower:
                # Extraire le numéro du match de groupe
                if "- 1" in round_name:
                    return "group_match_1"
                elif "- 2" in round_name:
                    return "group_match_2"
                elif "- 3" in round_name:
                    return "group_match_3"
                else:
                    return "group_stage"
            elif "round of 16" in round_lower or "1/8" in round_lower or "eighth" in round_lower:
                return "round_of_16"
            elif "quarter" in round_lower or "1/4" in round_lower:
                return "quarter_finals"
            elif "semi" in round_lower or "1/2" in round_lower:
                return "semi_finals"
            elif "final" in round_lower and "semi" not in round_lower:
                return "final"
            elif "3rd" in round_lower or "third" in round_lower:
                return "third_place"
            else:
                return "knockout_other"
        else:
            # Phases de league
            # Extraire le numéro de journée
            import re
            match = re.search(r'- (\d+)', round_name)
            if match:
                matchday = int(match.group(1))
                if matchday == 1:
                    return "matchday_1"
                elif matchday <= 10:
                    return "season_start"
                elif matchday <= 28:
                    return "season_middle"
                else:
                    return "season_end"
            else:
                return "regular_season"

    def analyze_penalty_patterns(
        self,
        events_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyse les patterns lies aux penalties.

        Returns:
            Dict avec penalties_won, penalties_conceded, conversion_rate
        """
        if events_df.empty:
            return {}

        # Penalties obtenus
        penalties_won = events_df[
            (events_df["is_our_team"] == True) &
            (events_df["detail"] == "Penalty")
        ]

        # Penalties concedes
        penalties_conceded = events_df[
            (events_df["is_our_team"] == False) &
            (events_df["detail"] == "Penalty")
        ]

        # Penalties rates (chercher "Missed Penalty" dans detail)
        penalties_missed = events_df[
            (events_df["is_our_team"] == True) &
            (events_df["detail"] == "Missed Penalty")
        ]

        penalties_scored = len(penalties_won) - len(penalties_missed)
        total_penalties = len(penalties_won)

        conversion_rate = (
            penalties_scored / total_penalties
            if total_penalties > 0 else 0
        )

        return {
            "penalties_won": total_penalties,
            "penalties_scored": penalties_scored,
            "penalties_missed": len(penalties_missed),
            "penalties_conceded": len(penalties_conceded),
            "conversion_rate": float(conversion_rate),
        }

    def analyze_regular_time_wins(
        self,
        matches_df: pd.DataFrame,
        events_df: pd.DataFrame,
        competition_id: int = None
    ) -> Dict[str, Any]:
        """
        Analyse les victoires obtenues en temps réglementaire (90 min) vs prolongations/penalties.

        Détecte si les victoires viennent du score à 90 minutes ou des prolongations/penalties.
        Insight clé : une équipe qui ne gagne jamais en temps réglementaire.

        Args:
            competition_id: Si fourni, filtre les matchs de cette compétition uniquement

        Returns:
            Dict avec wins_in_regular_time, wins_in_extra_time, regular_time_win_rate
        """
        if events_df.empty or matches_df.empty:
            return {}

        # Filtrer par compétition si demandé
        if competition_id is not None:
            matches_df = matches_df[matches_df["competition_id"] == competition_id]
            if matches_df.empty:
                return {}

        total_wins = 0
        wins_in_regular_time = 0
        wins_in_extra_time = 0

        for fixture_id in matches_df["fixture_id"].unique():
            # Vérifier si c'est une victoire
            match_result = matches_df[matches_df["fixture_id"] == fixture_id]["result"].values
            if len(match_result) == 0 or match_result[0] != "W":
                continue

            total_wins += 1

            # Récupérer tous les buts du match (avant 90 min)
            match_events = events_df[
                (events_df["fixture_id"] == fixture_id) &
                (events_df["type"] == "Goal") &
                (events_df["detail"].isin(["Normal Goal", "Penalty"])) &
                (events_df["minute"] < 120)  # Inclure prolongations
            ].sort_values("minute")

            # Calculer le score à 90 minutes
            score_us_at_90 = 0
            score_them_at_90 = 0

            for _, event in match_events.iterrows():
                minute = event["minute"]

                if minute < 90:
                    if event["is_our_team"]:
                        score_us_at_90 += 1
                    else:
                        score_them_at_90 += 1

            # Déterminer si la victoire vient du temps réglementaire
            if score_us_at_90 > score_them_at_90:
                # Victoire acquise à 90 min (temps réglementaire)
                wins_in_regular_time += 1
            else:
                # Victoire en prolongations ou penalties (nul à 90 min)
                wins_in_extra_time += 1

        if total_wins == 0:
            return {}

        regular_time_win_rate = wins_in_regular_time / total_wins if total_wins > 0 else 0

        return {
            "total_wins": total_wins,
            "wins_in_regular_time": wins_in_regular_time,
            "wins_in_extra_time": wins_in_extra_time,
            "regular_time_win_rate": float(regular_time_win_rate),
        }
