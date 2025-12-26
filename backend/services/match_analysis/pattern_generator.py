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

        return insights

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
