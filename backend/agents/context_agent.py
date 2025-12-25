"""
Context Agent - Manages match context lifecycle and caching

This agent checks if a match has already been analyzed and either:
1. Loads the existing context from cache (0 API calls)
2. Triggers new data collection and analysis (25 API calls)
"""
import logging
from typing import Dict, Any, Optional

from backend.core.context_manager import ContextManager
from backend.core.data_collector import DataCollector
from backend.store.match_context_store import MatchContextStore
from backend.store.schemas import MatchContext
from backend.analyzers import (
    Bet1X2Analyzer,
    BetGoalsAnalyzer,
    BetShotsAnalyzer,
    BetCornersAnalyzer,
    BetCardsTeamAnalyzer,
    BetCardPlayerAnalyzer,
    BetScorerAnalyzer,
    BetAssisterAnalyzer
)

logger = logging.getLogger(__name__)


class ContextAgent:
    """
    Agent responsible for match context management

    Key principle: Never analyze the same match twice
    - First access: Collect data (25 API calls) + Run analyzers + Save
    - Subsequent accesses: Load from cache (0 API calls)
    """

    def __init__(self, data_collector: DataCollector, storage_path: str = "./data/match_contexts"):
        self.collector = data_collector
        self.store = MatchContextStore(storage_path=storage_path)
        self.context_manager = ContextManager(self.store)

        # Initialize all 8 analyzers
        self.analyzers = {
            "1x2": Bet1X2Analyzer(),
            "goals": BetGoalsAnalyzer(),
            "shots": BetShotsAnalyzer(),
            "corners": BetCornersAnalyzer(),
            "cards_team": BetCardsTeamAnalyzer(),
            "card_player": BetCardPlayerAnalyzer(),
            "scorer": BetScorerAnalyzer(),
            "assister": BetAssisterAnalyzer()
        }

    async def get_match_context(self, fixture_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get match context (from cache or by collecting data)

        Args:
            fixture_id: ID of the fixture
            force_refresh: If True, ignore cache and collect fresh data

        Returns:
            Dictionary containing:
            - context: MatchContext object
            - source: "cache" or "fresh"
            - api_calls: Number of API calls made
        """
        # Check if we need new analysis
        needs_analysis = force_refresh or self.context_manager.needs_new_analysis(fixture_id)

        if not needs_analysis:
            logger.info(f"Loading match {fixture_id} from cache")
            context = self.context_manager.load_context(fixture_id)

            if context:
                return {
                    "context": context,
                    "source": "cache",
                    "api_calls": 0
                }

        # Collect fresh data
        logger.info(f"Collecting fresh data for match {fixture_id}")
        raw_data = await self.collector.collect_match_data(fixture_id)
        api_calls = raw_data.get("api_calls_count", 0)

        # Run all 8 analyzers
        logger.info("Running 8 analyzers")
        analyses = {}
        for bet_type, analyzer in self.analyzers.items():
            analysis_result = analyzer.analyze(raw_data)
            analyses[bet_type] = analysis_result
            coverage = "✓" if analysis_result.coverage_complete else "⚠"
            logger.debug(f"  {coverage} {bet_type}: {len(analysis_result.data_sources)} sources")

        # Save context
        context = self.context_manager.save_analysis(fixture_id, raw_data, analyses)
        logger.info(f"Context saved for {context.home_team} vs {context.away_team}")

        return {
            "context": context,
            "source": "fresh",
            "api_calls": api_calls
        }

    def get_cached_contexts(self) -> list[int]:
        """Get list of all cached fixture IDs"""
        return self.store.list_all_contexts()

    def get_bet_analysis(self, fixture_id: int, bet_type: str) -> Optional[Dict[str, Any]]:
        """
        Get specific bet analysis for a match

        Args:
            fixture_id: ID of the fixture
            bet_type: Type of bet (1x2, goals, shots, corners, cards_team, card_player, scorer, assister)

        Returns:
            Dictionary with indicators and data sources, or None if not found
        """
        context = self.store.get_context(fixture_id)

        if not context:
            return None

        analysis = context.analyses.get(bet_type)

        if not analysis:
            return None

        return {
            "indicators": analysis.indicators,
            "data_sources": analysis.data_sources,
            "coverage_complete": analysis.coverage_complete,
            "missing_sources": analysis.missing_sources
        }

    def update_causal_cache(self, fixture_id: int, payload: Dict[str, Any]) -> bool:
        """
        Update cached causal metrics/findings for a fixture if context exists.
        """
        context = self.store.get_context(fixture_id)
        if not context:
            return False

        context.causal_metrics = payload.get("calculated_metrics") or payload.get("metrics") or {}
        context.causal_findings = payload.get("rule_findings") or payload.get("findings") or []
        context.causal_confidence = payload.get("confidence_overall") or payload.get("confidence")
        context.causal_version = payload.get("version")

        self.store.save_context(context)
        return True
