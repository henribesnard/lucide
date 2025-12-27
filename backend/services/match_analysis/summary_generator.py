"""
Generateur de resume d'analyse de match en francais.
"""

from typing import Dict, List, Any
from datetime import datetime


class MatchSummaryGenerator:
    """Genere un resume formate en francais a partir des donnees d'analyse."""

    def generate_summary(self, analysis_data: Dict[str, Any]) -> str:
        """
        Genere un resume complet de l'analyse en format markdown.

        Args:
            analysis_data: Donnees d'analyse retournees par analyze_match_extended

        Returns:
            Resume formate en markdown
        """
        match = analysis_data.get("match", {})
        stats = analysis_data.get("statistics", {})
        insights_data = analysis_data.get("insights", {})
        metadata = analysis_data.get("metadata", {})

        team_a = match.get("team_a", "Équipe A")
        team_b = match.get("team_b", "Équipe B")
        league = match.get("league", "Compétition")
        season = match.get("season", datetime.now().year)

        # Construction du resume
        summary_parts = []

        # Header
        summary_parts.append(f"# Analyse Match : {team_a} vs {team_b}")
        summary_parts.append(f"## {league} {season}")
        summary_parts.append("")

        # Statistiques globales
        summary_parts.append("### 📊 Statistiques Globales")
        summary_parts.append("")
        summary_parts.append(self._format_team_stats(team_a, stats.get("team_a", {}), "toutes compétitions"))
        summary_parts.append("")
        summary_parts.append(self._format_team_stats(team_b, stats.get("team_b", {}), "toutes compétitions"))
        summary_parts.append("")

        # Statistiques specifiques a la competition
        team_a_comp_stats = stats.get("team_a", {}).get("competition_specific")
        team_b_comp_stats = stats.get("team_b", {}).get("competition_specific")

        if team_a_comp_stats or team_b_comp_stats:
            summary_parts.append(f"### 📊 Statistiques dans {league}")
            summary_parts.append("")
            if team_a_comp_stats:
                summary_parts.append(self._format_team_stats(team_a, team_a_comp_stats, f"{league} - toutes saisons"))
                summary_parts.append("")
            if team_b_comp_stats:
                summary_parts.append(self._format_team_stats(team_b, team_b_comp_stats, f"{league} - toutes saisons"))
                summary_parts.append("")

        # H2H
        h2h = stats.get("h2h", {})
        if h2h.get("total_matches", 0) > 0:
            summary_parts.append("**Historique H2H**")
            summary_parts.append(f"- {h2h.get('total_matches', 0)} confrontations récentes")
            summary_parts.append(f"- Victoires {team_a} : **{h2h.get('team_a_wins', 0)}**")

            team_a_wins = h2h.get('team_a_wins', 0)
            total_h2h = h2h.get('total_matches', 0)
            if team_a_wins > total_h2h / 2:
                summary_parts.append(f"- {team_a} domine les confrontations directes")
            elif team_a_wins < total_h2h / 2:
                summary_parts.append(f"- {team_b} domine les confrontations directes")
            else:
                summary_parts.append("- Équilibre dans les confrontations directes")
            summary_parts.append("")

        summary_parts.append("---")
        summary_parts.append("")

        # Insights
        summary_parts.append("### 🎯 Insights Clés")
        summary_parts.append("")

        insights = insights_data.get("items", [])
        high_insights = [i for i in insights if i.get("confidence") == "high"]
        medium_insights = [i for i in insights if i.get("confidence") == "medium"]

        if high_insights:
            summary_parts.append("#### ⚠️ Confiance ÉLEVÉE")
            summary_parts.append("")
            for i, insight in enumerate(high_insights, 1):
                summary_parts.append(f"{i}. **{self._get_insight_title(insight)}**")
                summary_parts.append(f"   - {insight.get('text', '')}")
                summary_parts.append(f"   - {self._get_insight_interpretation(insight)}")
                summary_parts.append("")

        if medium_insights:
            summary_parts.append("#### 📈 Confiance MOYENNE")
            summary_parts.append("")
            for i, insight in enumerate(medium_insights, len(high_insights) + 1):
                summary_parts.append(f"{i}. **{self._get_insight_title(insight)}**")
                summary_parts.append(f"   - {insight.get('text', '')}")
                summary_parts.append(f"   - {self._get_insight_interpretation(insight)}")
                summary_parts.append("")

        summary_parts.append("---")
        summary_parts.append("")

        # Tendances
        summary_parts.append("### 💡 Tendances et Patterns")
        summary_parts.append("")

        breakdown = insights_data.get("breakdown", {})

        summary_parts.append("**Par catégorie d'insights :**")
        by_category = breakdown.get("by_category", {})
        for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            category_label = self._translate_category(category)
            summary_parts.append(f"- {category_label} : {count} insight{'s' if count > 1 else ''}")
        summary_parts.append("")

        summary_parts.append("**Par type d'analyse :**")
        by_type = breakdown.get("by_type", {})
        for typ, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            type_label = self._translate_type(typ)
            summary_parts.append(f"- {type_label} : {count} insight{'s' if count > 1 else ''}")
        summary_parts.append("")

        summary_parts.append("---")
        summary_parts.append("")

        # Analyse technique
        summary_parts.append("### 🔍 Analyse Technique")
        summary_parts.append("")
        summary_parts.append("**Données analysées :**")
        summary_parts.append(f"- **{metadata.get('total_api_calls', 0)} appels API** vers API-Football v3")

        matches_analyzed = metadata.get("matches_analyzed", {})
        total_matches = matches_analyzed.get("team_a", 0) + matches_analyzed.get("team_b", 0)
        summary_parts.append(f"- **{total_matches} matchs** analysés ({matches_analyzed.get('team_a', 0)} + {matches_analyzed.get('team_b', 0)})")

        coverage = metadata.get("data_coverage", {})
        coverage_total = coverage.get("events", 0)
        summary_parts.append(f"- **{coverage_total} matchs** avec données complètes (événements, statistiques, compositions)")

        processing_time = metadata.get("processing_time_seconds", 0)
        summary_parts.append(f"- **Temps de traitement** : {processing_time:.2f} secondes")
        summary_parts.append("")

        summary_parts.append("**Période d'analyse :**")
        summary_parts.append(f"- Derniers {matches_analyzed.get('team_a', 30)} matchs par équipe (toutes compétitions)")
        if h2h.get("total_matches", 0) > 0:
            summary_parts.append(f"- {h2h.get('total_matches', 0)} confrontations directes récentes")
        summary_parts.append(f"- Saison {season}")
        summary_parts.append("")

        summary_parts.append("---")
        summary_parts.append("")

        # Conclusion
        summary_parts.append("### ✅ Conclusion")
        summary_parts.append("")
        summary_parts.append(self._generate_conclusion(team_a, team_b, stats, insights))
        summary_parts.append("")

        summary_parts.append("---")
        summary_parts.append("")

        # Footer
        total_insights = insights_data.get("total", 0)
        summary_parts.append(f"*Analyse générée par le système étendu avec algorithme complet (pandas/scipy/numpy) - {total_insights} insights détectés sur 39 patterns possibles*")

        return "\n".join(summary_parts)

    def _format_team_stats(self, team_name: str, stats: Dict[str, Any], label: str = "") -> str:
        """Formate les statistiques d'une equipe."""
        matches = stats.get("total_matches", 0)
        wins = stats.get("wins", 0)
        win_rate = stats.get("win_rate", 0)
        goals_per_match = stats.get("goals_per_match", 0)
        goals_against = stats.get("goals_against_per_match", 0)
        clean_sheet_rate = stats.get("clean_sheet_rate", 0)

        # Construire le label
        matches_label = f"{matches} matchs analysés"
        if label:
            matches_label += f" - {label}"

        lines = [
            f"**{team_name}** ({matches_label})",
            f"- Taux de victoire : **{win_rate:.1f}%** ({wins} victoires)",
            f"- Moyenne de buts marqués : **{goals_per_match:.2f} buts/match**",
            f"- Moyenne de buts encaissés : **{goals_against:.2f} buts/match**",
            f"- Clean sheets : **{clean_sheet_rate:.1f}%** des matchs",
        ]

        return "\n".join(lines)

    def _get_insight_title(self, insight: Dict[str, Any]) -> str:
        """Genere un titre pour l'insight."""
        category = insight.get("category", "")
        team = insight.get("team", "")

        titles = {
            "first_goal": "Premier but décisif",
            "form": "Forme exceptionnelle",
            "defense": "Solidité défensive",
            "comeback": "Capacité de renversement",
            "key_factor": "Facteur tactique",
            "discipline": "Impact de la discipline",
            "h2h_dominance": "Domination H2H",
        }

        title = titles.get(category, category.replace("_", " ").title())

        if team == "team_a":
            return title
        elif team == "team_b":
            return title
        else:
            return title

    def _get_insight_interpretation(self, insight: Dict[str, Any]) -> str:
        """Genere une interpretation de l'insight."""
        category = insight.get("category", "")

        interpretations = {
            "first_goal": "Le démarrage est crucial pour cette équipe",
            "form": "Une des meilleures formes actuelles",
            "defense": "Une défense particulièrement hermétique",
            "comeback": "Mentalité de combattant et résilience",
            "key_factor": "Un indicateur clé de performance",
            "discipline": "La discipline tactique est déterminante",
            "h2h_dominance": "Un ascendant psychologique important",
        }

        return interpretations.get(category, "Facteur à prendre en compte")

    def _translate_category(self, category: str) -> str:
        """Traduit une categorie en francais."""
        translations = {
            "first_goal": "Premier but",
            "defense": "Défense",
            "form": "Forme générale",
            "comeback": "Comebacks",
            "key_factor": "Facteur clé",
            "discipline": "Discipline",
            "h2h_dominance": "Domination H2H",
            "h2h_patterns": "Patterns H2H",
            "timing": "Timing des buts",
            "key_player": "Joueur clé",
            "synergy": "Synergies",
            "availability": "Disponibilité",
        }

        return translations.get(category, category.replace("_", " ").title())

    def _translate_type(self, typ: str) -> str:
        """Traduit un type en francais."""
        translations = {
            "events": "Événements (timeline)",
            "statistical": "Statistiques globales",
            "statistical_correlation": "Corrélations statistiques",
            "player_impact": "Impact joueurs",
            "player_synergy": "Synergies joueurs",
            "h2h": "Historique H2H",
        }

        return translations.get(typ, typ.replace("_", " ").title())

    def _generate_conclusion(
        self,
        team_a: str,
        team_b: str,
        stats: Dict[str, Any],
        insights: List[Dict[str, Any]]
    ) -> str:
        """Genere une conclusion basee sur les statistiques et insights."""
        team_a_stats = stats.get("team_a", {})
        team_b_stats = stats.get("team_b", {})

        team_a_win_rate = team_a_stats.get("win_rate", 0)
        team_b_win_rate = team_b_stats.get("win_rate", 0)

        # Determiner le favori
        if team_a_win_rate > team_b_win_rate + 15:
            favorite = team_a
            underdog = team_b
            fav_wr = team_a_win_rate
        elif team_b_win_rate > team_a_win_rate + 15:
            favorite = team_b
            underdog = team_a
            fav_wr = team_b_win_rate
        else:
            return (
                f"Match équilibré entre **{team_a}** ({team_a_win_rate:.1f}% de victoires) "
                f"et **{team_b}** ({team_b_win_rate:.1f}% de victoires). "
                f"Les deux équipes affichent des statistiques comparables."
            )

        # Trouver un insight cle sur le favori
        key_insight = None
        for insight in insights:
            if "100%" in insight.get("text", "") and insight.get("confidence") == "high":
                key_insight = insight.get("text", "")
                break

        conclusion = (
            f"Le **{favorite}** part "
            f"{'largement ' if fav_wr > 70 else ''}favori avec une forme "
            f"{'exceptionnelle' if fav_wr > 80 else 'solide'} "
            f"({fav_wr:.0f}% de victoires). "
            f"Le **{underdog}** reste dangereux mais affiche des statistiques "
            f"{'nettement ' if abs(team_a_win_rate - team_b_win_rate) > 25 else ''}inférieures."
        )

        if key_insight:
            conclusion += f"\n\n**Facteur déterminant** : {key_insight}"

        return conclusion
