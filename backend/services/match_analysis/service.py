"""
Service principal d'analyse de match.
Orchestre toutes les etapes de l'algorithme.
"""

import logging
import time
from datetime import datetime
from backend.api.football_api import FootballAPIClient
from .types import MatchAnalysisInput, MatchAnalysisResult
from .data_collector import DataCollector
from .feature_builder import FeatureBuilder
from .feature_builder_v2 import FeatureBuilderV2
from .pattern_analyzer import PatternAnalyzer
from .pattern_generator import PatternGenerator
from .insight_formatter import InsightFormatter
from .summary_generator import MatchSummaryGenerator

logger = logging.getLogger(__name__)


class MatchAnalysisService:
    """
    Service d'analyse de match pour detecter des assets caches.

    Implemente l'algorithme complet:
    - Etape 0: Normaliser les identifiants
    - Etape 1: Definir le perimetre de donnees
    - Etape 2: Collecter les donnees
    - Etape 3: Construire les features
    - Etape 4: Generer des patterns candidats
    - Etape 5: Mesurer la force des patterns
    - Etape 6: Selectionner les "assets caches"
    - Etape 7: Restituer l'insight
    """

    def __init__(
        self,
        api_client: FootballAPIClient,
        min_sample_size: int = 6,
        min_delta_baseline: float = 20.0,
        extreme_threshold: float = 95.0,
        strong_threshold: float = 80.0,
    ):
        self.api_client = api_client
        self.data_collector = DataCollector(api_client)
        self.feature_builder = FeatureBuilder()
        self.feature_builder_v2 = FeatureBuilderV2()
        self.pattern_analyzer = PatternAnalyzer(
            min_sample_size=min_sample_size,
            min_delta_baseline=min_delta_baseline,
            extreme_threshold=extreme_threshold,
            strong_threshold=strong_threshold,
        )
        self.pattern_generator = PatternGenerator()
        self.insight_formatter = InsightFormatter()
        self.summary_generator = MatchSummaryGenerator()

    async def analyze_match(
        self, input_data: MatchAnalysisInput
    ) -> MatchAnalysisResult:
        """
        Execute l'analyse complete d'un match.

        Args:
            input_data: Parametres d'entree

        Returns:
            MatchAnalysisResult avec tous les insights detectes
        """
        logger.info("="*80)
        logger.info("DEBUT ANALYSE DE MATCH")
        logger.info(f"League: {input_data.league}, Teams: {input_data.team_a} vs {input_data.team_b}")
        logger.info("="*80)

        start_time = time.time()
        warnings = []

        try:
            # ETAPE 0: Normaliser les identifiants
            normalized = await self.data_collector.normalize_identifiers(input_data)

            # Verifier la couverture
            if not normalized.coverage.statistics_fixtures:
                warnings.append(
                    "Statistics fixtures non disponibles - analyse limitee"
                )
            if not normalized.coverage.lineups:
                warnings.append("Lineups non disponibles - pas d'analyse de composition")

            # ETAPE 1: Definir le perimetre
            scope = await self.data_collector.define_data_scope(
                normalized, input_data.num_seasons_history
            )

            # ETAPE 2: Collecter les donnees
            data = await self.data_collector.collect_data(normalized, scope)

            # ETAPE 3: Construire les features
            features = self.feature_builder.build_features(data, normalized, input_data)

            # ETAPE 4: Generer les patterns candidats
            all_patterns = self.pattern_analyzer.generate_patterns(
                features, input_data, normalized
            )

            # ETAPE 5: Mesurer la force des patterns
            scored_patterns = self.pattern_analyzer.score_patterns(all_patterns, scope)

            # ETAPE 6: Selectionner les assets caches
            filtered_patterns = self.pattern_analyzer.filter_hidden_assets(scored_patterns)

            # ETAPE 7: Formater les insights
            hidden_assets = self.insight_formatter.format_insights(
                filtered_patterns, normalized
            )

            # Construire le resultat
            processing_time = time.time() - start_time

            result = MatchAnalysisResult(
                input=input_data,
                normalized_ids=normalized,
                features=features,
                all_patterns=all_patterns,
                hidden_assets=hidden_assets,
                analysis_timestamp=datetime.utcnow(),
                total_api_calls=self.data_collector.api_call_count,
                processing_time_seconds=processing_time,
                warnings=warnings,
            )

            logger.info("="*80)
            logger.info("FIN ANALYSE DE MATCH")
            logger.info(f"Patterns generes: {len(all_patterns)}")
            logger.info(f"Assets caches detectes: {len(hidden_assets)}")
            logger.info(f"API calls: {result.total_api_calls}")
            logger.info(f"Temps de traitement: {processing_time:.2f}s")
            logger.info("="*80)

            return result

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse: {e}", exc_info=True)
            raise

    async def analyze_match_quick(
        self, input_data: MatchAnalysisInput
    ) -> MatchAnalysisResult:
        """
        Version rapide de l'analyse (1 saison uniquement).

        Args:
            input_data: Parametres d'entree

        Returns:
            MatchAnalysisResult avec analyse rapide
        """
        input_data.num_seasons_history = 1
        return await self.analyze_match(input_data)

    async def analyze_match_extended(
        self,
        input_data: MatchAnalysisInput,
        num_last_matches: int = 30
    ) -> dict:
        """
        Analyse etendue avec algorithme complet (toutes competitions).

        Utilise le nouveau systeme avec:
        - 30 derniers matchs par equipe (toutes competitions)
        - Events detailles (timeline, buts, cartons)
        - Stats match par match (possession, tirs, passes)
        - Lineups (compositions, remplacements)
        - Analyses statistiques avancees (pandas/scipy)
        - Detection de patterns avances (39 types)
        - Impact joueurs et synergies
        - Confrontations coaches

        Args:
            input_data: Parametres d'entree
            num_last_matches: Nombre de derniers matchs a analyser (defaut: 30)

        Returns:
            Dict avec insights complets et statistiques
        """
        logger.info("="*80)
        logger.info("DEBUT ANALYSE ETENDUE")
        logger.info(f"League: {input_data.league}, Teams: {input_data.team_a} vs {input_data.team_b}")
        logger.info(f"Perimetre: {num_last_matches} derniers matchs (toutes competitions)")
        logger.info("="*80)

        start_time = time.time()

        try:
            # ETAPE 0: Normaliser les identifiants
            logger.info("Etape 0: Normalisation des identifiants...")
            normalized = await self.data_collector.normalize_identifiers(input_data)

            # ETAPE 1: Definir le perimetre etendu
            logger.info(f"Etape 1: Definition du perimetre ({num_last_matches} matchs)...")
            scope = await self.data_collector.define_data_scope_extended(
                normalized,
                num_last_matches=num_last_matches
            )

            # ETAPE 2: Collecter les donnees (enrichi)
            logger.info("Etape 2: Collecte des donnees (events + stats + lineups)...")
            data = await self.data_collector.collect_data_extended(normalized, scope)

            # ETAPE 3: Construire les features (avancees)
            logger.info("Etape 3: Construction des features avancees...")
            features = self.feature_builder_v2.build_all_features(data, normalized)

            # ETAPE 4: Generer les insights
            logger.info("Etape 4: Generation des insights...")
            insights = self.pattern_generator.generate_insights(
                features,
                normalized.team_a_name,
                normalized.team_b_name
            )

            processing_time = time.time() - start_time

            # Statistiques des equipes
            team_a_stats = features["team_a"]["statistical"]
            team_b_stats = features["team_b"]["statistical"]
            h2h_stats = features["h2h"]

            # Breakdown des insights
            by_type = {}
            by_confidence = {}
            by_category = {}
            by_team = {}

            for insight in insights:
                # Par type
                itype = insight["type"]
                by_type[itype] = by_type.get(itype, 0) + 1

                # Par confiance
                conf = insight["confidence"]
                by_confidence[conf] = by_confidence.get(conf, 0) + 1

                # Par categorie
                cat = insight["category"]
                by_category[cat] = by_category.get(cat, 0) + 1

                # Par equipe
                team = insight.get("team", "both")
                by_team[team] = by_team.get(team, 0) + 1

            # Construire le resultat
            result = {
                "success": True,
                "analysis_type": "extended",
                "match": {
                    "league": normalized.league_name,
                    "league_id": normalized.league_id,
                    "season": normalized.season,
                    "team_a": normalized.team_a_name,
                    "team_a_id": normalized.team_a_id,
                    "team_b": normalized.team_b_name,
                    "team_b_id": normalized.team_b_id,
                },
                "statistics": {
                    "team_a": {
                        "total_matches": team_a_stats.get("total_matches", 0),
                        "wins": team_a_stats.get("wins", 0),
                        "win_rate": round(team_a_stats.get("win_rate", 0) * 100, 1),
                        "goals_per_match": round(team_a_stats.get("goals_per_match", 0), 2),
                        "goals_against_per_match": round(team_a_stats.get("goals_against_per_match", 0), 2),
                        "clean_sheet_rate": round(team_a_stats.get("clean_sheet_rate", 0) * 100, 1),
                    },
                    "team_b": {
                        "total_matches": team_b_stats.get("total_matches", 0),
                        "wins": team_b_stats.get("wins", 0),
                        "win_rate": round(team_b_stats.get("win_rate", 0) * 100, 1),
                        "goals_per_match": round(team_b_stats.get("goals_per_match", 0), 2),
                        "goals_against_per_match": round(team_b_stats.get("goals_against_per_match", 0), 2),
                        "clean_sheet_rate": round(team_b_stats.get("clean_sheet_rate", 0) * 100, 1),
                    },
                    "h2h": {
                        "total_matches": h2h_stats.get("total_matches", 0),
                        "team_a_wins": h2h_stats.get("team_a_wins", 0),
                    },
                },
                "insights": {
                    "total": len(insights),
                    "items": insights[:20],  # Top 20 insights
                    "breakdown": {
                        "by_type": by_type,
                        "by_confidence": by_confidence,
                        "by_category": by_category,
                        "by_team": by_team,
                    },
                },
                "metadata": {
                    "total_api_calls": self.data_collector.api_call_count,
                    "processing_time_seconds": round(processing_time, 2),
                    "matches_analyzed": {
                        "team_a": len(data["team_a_all_matches"]),
                        "team_b": len(data["team_b_all_matches"]),
                        "h2h": len(data["h2h_matches"]),
                    },
                    "data_coverage": {
                        "events": len(data["events_by_fixture"]),
                        "stats": len(data["stats_by_fixture"]),
                        "lineups": len(data["lineups_by_fixture"]),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            # Generer le resume en francais
            logger.info("Etape 5: Generation du resume...")
            summary = self.summary_generator.generate_summary(result)
            result["summary"] = summary

            logger.info("="*80)
            logger.info("FIN ANALYSE ETENDUE")
            logger.info(f"Insights generes: {len(insights)}")
            logger.info(f"API calls: {self.data_collector.api_call_count}")
            logger.info(f"Temps de traitement: {processing_time:.2f}s")
            logger.info("="*80)

            return result

        except Exception as e:
            logger.error(f"Erreur lors de l'analyse etendue: {e}", exc_info=True)
            raise

    def get_analysis_stats(self) -> dict:
        """
        Retourne des statistiques sur le service.

        Returns:
            Dict avec statistiques
        """
        return {
            "total_api_calls": self.data_collector.api_call_count,
            "service_name": "MatchAnalysisService",
            "version": "1.0.0",
        }
