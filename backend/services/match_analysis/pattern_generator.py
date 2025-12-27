"""
Pattern Generator - Version simplifiee.
Genere les insights a partir des features analysees.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PatternGenerator:
    """Genere les patterns/insights a partir des features."""

    def generate_insights(
        self,
        features: Dict[str, Any],
        team_a_name: str,
        team_b_name: str
    ) -> List[Dict[str, Any]]:
        """
        Genere tous les insights a partir des features.

        Returns:
            Liste d'insights avec texte, confiance, categorie
        """
        insights = []

        # 1) Insights statistiques team A
        insights.extend(self._generate_statistical_insights(
            features["team_a"]["statistical"],
            team_a_name,
            "team_a"
        ))

        # 2) Insights statistiques team B
        insights.extend(self._generate_statistical_insights(
            features["team_b"]["statistical"],
            team_b_name,
            "team_b"
        ))

        # 3) Insights events team A
        insights.extend(self._generate_events_insights(
            features["team_a"]["events"],
            team_a_name,
            "team_a"
        ))

        # 4) Insights events team B
        insights.extend(self._generate_events_insights(
            features["team_b"]["events"],
            team_b_name,
            "team_b"
        ))

        # 3b) Insights events competition-specific team A
        insights.extend(self._generate_competition_events_insights(
            features["team_a"].get("events_competition", {}),
            features["team_a"]["statistical"],
            team_a_name,
            "team_a"
        ))

        # 4b) Insights events competition-specific team B
        insights.extend(self._generate_competition_events_insights(
            features["team_b"].get("events_competition", {}),
            features["team_b"]["statistical"],
            team_b_name,
            "team_b"
        ))

        # 5) Insights joueurs team A
        insights.extend(self._generate_player_insights(
            features["team_a"]["players"],
            team_a_name,
            "team_a"
        ))

        # 6) Insights joueurs team B
        insights.extend(self._generate_player_insights(
            features["team_b"]["players"],
            team_b_name,
            "team_b"
        ))

        # 7) Insights H2H
        insights.extend(self._generate_h2h_insights(
            features["h2h"],
            team_a_name,
            team_b_name
        ))

        # Trier par impact/importance
        insights.sort(key=lambda x: self._calculate_importance(x), reverse=True)

        return insights

    def _generate_statistical_insights(self, stats, team_name, team_key):
        """Genere insights statistiques."""
        insights = []

        if not stats:
            return insights

        # CROSS-CHECK: Regular time wins dans la competition specifique
        # Combine competition_specific with regular_time_wins to detect teams that
        # win in competition but ONLY via extra time/penalties
        comp_specific = stats.get("competition_specific", {})
        if comp_specific.get("has_competition_data", False):
            # This will be filled later after events insights are processed
            # Store it for potential cross-checking
            pass

        # Win rate global
        if stats.get("win_rate", 0) >= 0.7:
            insights.append({
                "type": "statistical",
                "team": team_key,
                "text": f"{team_name} gagne {stats['win_rate']*100:.0f}% de ses matchs "
                        f"({stats['wins']}/{stats['total_matches']}). Excellente forme.",
                "confidence": "high",
                "category": "form",
                "metric_value": stats["win_rate"],
            })

        # Clean sheets
        if stats.get("clean_sheet_rate", 0) >= 0.5:
            insights.append({
                "type": "statistical",
                "team": team_key,
                "text": f"{team_name} garde sa cage inviolee dans {stats['clean_sheet_rate']*100:.0f}% "
                        f"de ses matchs. Defense solide.",
                "confidence": "medium",
                "category": "defense",
                "metric_value": stats["clean_sheet_rate"],
            })

        # Correlations significatives
        correlations = stats.get("correlations", {})
        for stat_name, (corr, p_value) in correlations.items():
            if p_value < 0.05 and abs(corr) > 0.5:
                insights.append({
                    "type": "statistical_correlation",
                    "team": team_key,
                    "text": f"Pour {team_name}, {stat_name} correle fortement avec victoires "
                            f"(r={corr:.2f}, p<0.05). Facteur cle.",
                    "confidence": "high",
                    "category": "key_factor",
                    "metric_value": abs(corr),
                })

        # Comparaison stats competition vs stats globales
        comp_specific = stats.get("competition_specific", {})
        logger.info(f"[{team_name}] Competition specific data: has_data={comp_specific.get('has_competition_data', False)}")
        if comp_specific.get("has_competition_data", False):
            in_comp = comp_specific["in_competition"]
            global_stats = comp_specific["global"]
            logger.info(f"[{team_name}] In competition: {in_comp['total_matches']} matches, {in_comp['wins']} wins ({in_comp['win_rate']*100:.1f}%)")
            logger.info(f"[{team_name}] Global: {global_stats['total_matches']} matches, {global_stats['wins']} wins ({global_stats['win_rate']*100:.1f}%)")

            # Comparaison win rate
            if in_comp["total_matches"] >= 3:  # Au moins 3 matchs dans la competition
                comp_wr = in_comp["win_rate"]
                global_wr = global_stats["win_rate"]
                delta = comp_wr - global_wr
                logger.info(f"[{team_name}] Win rate delta: {delta*100:.1f}% (threshold: ±20%)")

                if abs(delta) >= 0.20:  # Difference d'au moins 20%
                    if delta < -0.20:
                        # Moins bon dans la competition
                        insights.append({
                            "type": "statistical",
                            "team": team_key,
                            "text": f"{team_name} dans cette competition: {comp_wr*100:.0f}% victoires "
                                    f"({in_comp['wins']}/{in_comp['total_matches']}), "
                                    f"contre {global_wr*100:.0f}% globalement. Perf inferieure.",
                            "confidence": "high",
                            "category": "competition_form",
                            "metric_value": abs(delta),
                        })
                    else:
                        # Meilleur dans la competition
                        insights.append({
                            "type": "statistical",
                            "team": team_key,
                            "text": f"{team_name} dans cette competition: {comp_wr*100:.0f}% victoires "
                                    f"({in_comp['wins']}/{in_comp['total_matches']}), "
                                    f"contre {global_wr*100:.0f}% globalement. Specialiste.",
                            "confidence": "high",
                            "category": "competition_form",
                            "metric_value": delta,
                        })

        return insights

    def _generate_events_insights(self, events, team_name, team_key):
        """Genere insights events."""
        insights = []

        if not events:
            return insights

        # First goal impact
        first_goal = events.get("first_goal", {})
        if first_goal.get("scored_first_count", 0) > 0:
            win_rate_scored = first_goal.get("win_rate_when_scored_first", 0)
            if win_rate_scored >= 0.75:
                insights.append({
                    "type": "events",
                    "team": team_key,
                    "text": f"{team_name} gagne {win_rate_scored*100:.0f}% quand marque en premier "
                            f"({first_goal['wins_when_scored_first']}/{first_goal['scored_first_count']}). "
                            f"Demarrage crucial.",
                    "confidence": "high",
                    "category": "first_goal",
                    "metric_value": win_rate_scored,
                })

        # Comebacks
        comebacks = events.get("comebacks", {})
        if comebacks.get("comeback_attempts", 0) > 0:
            comeback_rate = comebacks.get("comeback_rate", 0)
            if comeback_rate >= 0.5:
                insights.append({
                    "type": "events",
                    "team": team_key,
                    "text": f"{team_name} renverse {comeback_rate*100:.0f}% des matchs ou mene "
                            f"({comebacks['comeback_successes']}/{comebacks['comeback_attempts']}). "
                            f"Mentalite forte.",
                    "confidence": "medium",
                    "category": "comeback",
                    "metric_value": comeback_rate,
                })

        # Early cards impact
        early_cards = events.get("early_cards", {})
        if early_cards.get("sample_with_early_card", 0) >= 3:
            delta = early_cards.get("delta", 0)
            if delta < -0.20:  # Impact negatif fort
                insights.append({
                    "type": "events",
                    "team": team_key,
                    "text": f"{team_name} ne gagne que {early_cards['win_rate_with_early_card']*100:.0f}% "
                            f"avec carton avant 30 min, contre {early_cards['win_rate_without_early_card']*100:.0f}% "
                            f"sans. Discipline critique.",
                    "confidence": "medium",
                    "category": "discipline",
                    "metric_value": abs(delta),
                })

        # Goals heatmap
        heatmap = events.get("goals_heatmap", {})
        if heatmap.get("most_prolific_percentage", 0) >= 35:
            insights.append({
                "type": "events",
                "team": team_key,
                "text": f"{team_name} marque {heatmap['most_prolific_percentage']:.0f}% de ses buts "
                        f"en periode {heatmap['most_prolific_period']}. Periode dangereuse.",
                "confidence": "medium",
                "category": "timing",
                "metric_value": heatmap["most_prolific_percentage"],
            })

        # Regular time wins (détection équipes qui gagnent uniquement en prolongations/penalties)
        regular_time = events.get("regular_time_wins", {})
        logger.info(f"[{team_name}] Regular time wins data: {regular_time}")
        if regular_time.get("total_wins", 0) >= 3:  # Au moins 3 victoires pour être significatif
            regular_rate = regular_time.get("regular_time_win_rate", 1.0)
            logger.info(f"[{team_name}] Regular time win rate: {regular_rate}")

            if regular_rate == 0:
                # Jamais gagné en temps réglementaire
                insights.append({
                    "type": "events",
                    "team": team_key,
                    "text": f"{team_name} n'a JAMAIS gagne en temps reglementaire "
                            f"({regular_time['wins_in_extra_time']} victoires uniquement en prolongations/penalties). "
                            f"Equipe de prolongations.",
                    "confidence": "high",
                    "category": "regular_time",
                    "metric_value": 0.0,
                })
            elif regular_rate <= 0.33:
                # Gagne rarement en temps réglementaire (<= 33%)
                insights.append({
                    "type": "events",
                    "team": team_key,
                    "text": f"{team_name} gagne seulement {regular_rate*100:.0f}% en temps reglementaire "
                            f"({regular_time['wins_in_regular_time']}/{regular_time['total_wins']}). "
                            f"Souvent en prolongations.",
                    "confidence": "medium",
                    "category": "regular_time",
                    "metric_value": regular_rate,
                })

        return insights

    def _generate_competition_events_insights(self, events_comp, stats, team_name, team_key):
        """Genere insights events specifiques a la competition."""
        insights = []

        if not events_comp or not stats:
            return insights

        # Verifier qu'on a des donnees competition
        comp_specific = stats.get("competition_specific", {})
        if not comp_specific.get("has_competition_data", False):
            return insights

        competition_name = "cette competition"  # On pourrait passer le nom en param

        # Regular time wins dans la competition
        regular_time = events_comp.get("regular_time_wins", {})
        total_wins_comp = regular_time.get("total_wins", 0)
        logger.info(f"[{team_name}] Competition-specific regular time wins: {regular_time}")

        if total_wins_comp >= 1:  # Au moins 1 victoire dans la competition
            regular_rate_comp = regular_time.get("regular_time_win_rate", 1.0)
            wins_in_regular = regular_time.get("wins_in_regular_time", 0)
            wins_in_extra = regular_time.get("wins_in_extra_time", 0)

            if regular_rate_comp == 0:
                # JAMAIS gagné en temps réglementaire dans cette compétition
                insights.append({
                    "type": "events_competition",
                    "team": team_key,
                    "text": f"{team_name} n'a JAMAIS gagne en temps reglementaire dans {competition_name} "
                            f"({wins_in_extra} victoire(s) uniquement en prolongations/penalties). "
                            f"Equipe de prolongations en competition.",
                    "confidence": "high",
                    "category": "competition_regular_time",
                    "metric_value": 1.0,  # High metric for "never"
                })
            elif regular_rate_comp <= 0.33 and total_wins_comp >= 3:
                # Gagne rarement en temps réglementaire dans la compétition
                insights.append({
                    "type": "events_competition",
                    "team": team_key,
                    "text": f"{team_name} dans {competition_name}: seulement {regular_rate_comp*100:.0f}% "
                            f"victoires en temps reglementaire ({wins_in_regular}/{total_wins_comp}). "
                            f"Souvent en prolongations.",
                    "confidence": "medium",
                    "category": "competition_regular_time",
                    "metric_value": 1.0 - regular_rate_comp,
                })

        # NOUVEAU: Analyse par phase de compétition
        by_phase = events_comp.get("by_phase", {})
        logger.info(f"[{team_name}] Phases analysis: {list(by_phase.keys())}")

        for phase, phase_stats in by_phase.items():
            total_matches = phase_stats.get("total_matches", 0)
            wins = phase_stats.get("wins", 0)
            win_rate = phase_stats.get("win_rate", 0)

            # Seuil minimum: au moins 3 matchs dans cette phase
            if total_matches < 3:
                continue

            # Patterns à détecter
            if win_rate >= 0.75:  # Gagne >= 75% dans cette phase
                phase_name = self._format_phase_name(phase)
                insights.append({
                    "type": "phase_performance",
                    "team": team_key,
                    "text": f"{team_name} domine en {phase_name}: {win_rate*100:.0f}% victoires "
                            f"({wins}/{total_matches}). Phase forte.",
                    "confidence": "high" if win_rate >= 0.9 else "medium",
                    "category": "phase_dominance",
                    "metric_value": win_rate,
                })
            elif win_rate == 0 and total_matches >= 3:  # Jamais gagné dans cette phase
                phase_name = self._format_phase_name(phase)
                insights.append({
                    "type": "phase_performance",
                    "team": team_key,
                    "text": f"{team_name} n'a JAMAIS gagne en {phase_name} "
                            f"(0/{total_matches}). Bloque a cette phase.",
                    "confidence": "high",
                    "category": "phase_weakness",
                    "metric_value": 1.0,
                })
            elif win_rate <= 0.25 and total_matches >= 4:  # Faible dans cette phase
                phase_name = self._format_phase_name(phase)
                insights.append({
                    "type": "phase_performance",
                    "team": team_key,
                    "text": f"{team_name} faible en {phase_name}: {win_rate*100:.0f}% victoires "
                            f"({wins}/{total_matches}). Phase critique.",
                    "confidence": "medium",
                    "category": "phase_weakness",
                    "metric_value": 1.0 - win_rate,
                })

        return insights

    def _format_phase_name(self, phase_key: str) -> str:
        """Formate le nom de phase pour l'affichage."""
        phase_names = {
            "group_match_1": "1er match de groupe",
            "group_match_2": "2ème match de groupe",
            "group_match_3": "3ème match de groupe",
            "group_stage": "phase de groupes",
            "round_of_16": "huitièmes de finale",
            "quarter_finals": "quarts de finale",
            "semi_finals": "demi-finales",
            "final": "finale",
            "third_place": "match pour la 3ème place",
            "matchday_1": "journée 1",
            "season_start": "début de saison",
            "season_middle": "milieu de saison",
            "season_end": "fin de saison",
        }
        return phase_names.get(phase_key, phase_key.replace("_", " "))

    def _generate_player_insights(self, players, team_name, team_key):
        """Genere insights joueurs."""
        insights = []

        if not players:
            return insights

        # Impact joueurs
        player_impacts = players.get("player_impacts", [])
        for impact in player_impacts:
            delta = impact.get("delta", 0)
            if abs(delta) >= 0.20:  # +/- 20 points
                if delta > 0:
                    insights.append({
                        "type": "player_impact",
                        "team": team_key,
                        "text": f"{team_name} avec {impact['player_name']} titulaire: "
                                f"{impact['win_rate_with']*100:.0f}% win rate "
                                f"({impact['wins_with']}/{impact['matches_with']}), "
                                f"contre {impact['win_rate_without']*100:.0f}% sans lui. "
                                f"Joueur cle (+{delta*100:.0f} pts).",
                        "confidence": "high",
                        "category": "key_player",
                        "metric_value": delta,
                    })
                else:
                    insights.append({
                        "type": "player_impact",
                        "team": team_key,
                        "text": f"{team_name} sans {impact['player_name']}: "
                                f"{impact['win_rate_without']*100:.0f}% win rate "
                                f"({impact['wins_without']}/{impact['matches_without']}), "
                                f"contre {impact['win_rate_with']*100:.0f}% avec lui. "
                                f"Meilleur sans lui ({delta*100:.0f} pts).",
                        "confidence": "medium",
                        "category": "player_negative",
                        "metric_value": abs(delta),
                    })

        # Synergies
        synergies = players.get("synergies", [])
        for synergy in synergies[:3]:  # Top 3
            delta = synergy.get("delta", 0)
            if delta > 0:
                insights.append({
                    "type": "player_synergy",
                    "team": team_key,
                    "text": f"{team_name} avec duo {synergy['player1_name']}-{synergy['player2_name']}: "
                            f"{synergy['win_rate_together']*100:.0f}% win rate "
                            f"({synergy['wins_together']}/{synergy['matches_together']}), "
                            f"contre {synergy['win_rate_separate']*100:.0f}% sans ce duo. "
                            f"Synergie (+{delta*100:.0f} pts).",
                    "confidence": "high",
                    "category": "synergy",
                    "metric_value": delta,
                })

        # Disponibilite
        availability = players.get("availability", {})
        if availability.get("total_unavailable", 0) > 0:
            injured = availability.get("injured_key_players", [])
            suspended = availability.get("suspended_key_players", [])

            if injured:
                names = ", ".join([p["player_name"] for p in injured])
                insights.append({
                    "type": "player_availability",
                    "team": team_key,
                    "text": f"{team_name}: Joueur(s) cle(s) blesse(s): {names}. Impact potentiel.",
                    "confidence": "high",
                    "category": "availability",
                    "metric_value": len(injured),
                })

            if suspended:
                names = ", ".join([p["player_name"] for p in suspended])
                insights.append({
                    "type": "player_availability",
                    "team": team_key,
                    "text": f"{team_name}: Joueur(s) cle(s) suspendu(s): {names}. Impact potentiel.",
                    "confidence": "high",
                    "category": "availability",
                    "metric_value": len(suspended),
                })

        return insights

    def _generate_h2h_insights(self, h2h, team_a_name, team_b_name):
        """Genere insights H2H."""
        insights = []

        total = h2h.get("total_matches", 0)
        if total == 0:
            return insights

        team_a_wins = h2h.get("team_a_wins", 0)
        win_rate = team_a_wins / total if total > 0 else 0

        if win_rate == 0 and total >= 3:
            insights.append({
                "type": "h2h",
                "team": "both",
                "text": f"{team_a_name} n'a jamais battu {team_b_name} en H2H "
                        f"(0V sur {total} matchs). Domination historique de {team_b_name}.",
                "confidence": "high",
                "category": "h2h_dominance",
                "metric_value": 1.0,
            })
        elif win_rate >= 0.75 and total >= 4:
            insights.append({
                "type": "h2h",
                "team": "both",
                "text": f"{team_a_name} domine le H2H: {team_a_wins}/{total} victoires "
                        f"({win_rate*100:.0f}%). Avantage psychologique.",
                "confidence": "high",
                "category": "h2h_dominance",
                "metric_value": win_rate,
            })

        return insights

    def _calculate_importance(self, insight):
        """Calcule l'importance d'un insight pour tri."""
        score = 0

        # Confiance
        if insight["confidence"] == "high":
            score += 3
        elif insight["confidence"] == "medium":
            score += 2
        else:
            score += 1

        # Metric value
        metric = insight.get("metric_value", 0)
        score += metric * 2

        # Categories prioritaires
        priority_categories = ["key_player", "h2h_dominance", "synergy", "key_factor"]
        if insight["category"] in priority_categories:
            score += 2

        return score
