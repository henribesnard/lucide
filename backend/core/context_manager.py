"""
Context Manager - Manages match context cache

Principle: A match is analyzed once, then all questions use the cached context.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from backend.store.match_context_store import MatchContextStore
from backend.store.schemas import MatchContext, MatchMetadata, BetAnalysisData

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages match context lifecycle

    Responsibilities:
    - Check if match context exists
    - Load context from store
    - Save new context
    - Maintain current conversation context
    """

    def __init__(self, store: MatchContextStore):
        self.store = store
        self.current_match_context: Optional[MatchContext] = None

    def needs_new_analysis(self, fixture_id: int) -> bool:
        """
        Determine if a new analysis is required

        Args:
            fixture_id: ID of the fixture

        Returns:
            True if match needs to be analyzed (not in cache)
        """
        exists = self.store.has_context(fixture_id)

        if exists:
            logger.info(f"Match {fixture_id} already analyzed (cache hit)")
        else:
            logger.info(f"Match {fixture_id} not analyzed yet (cache miss)")

        return not exists

    def load_context(self, fixture_id: int) -> Optional[MatchContext]:
        """
        Load match context from store

        Args:
            fixture_id: ID of the fixture

        Returns:
            MatchContext if found, None otherwise
        """
        context = self.store.get_context(fixture_id)

        if context:
            self.current_match_context = context
            logger.info(
                f"Context loaded: {context.home_team} vs {context.away_team} "
                f"(accessed {context.metadata.access_count} times)"
            )
        else:
            logger.warning(f"No context found for fixture {fixture_id}")

        return context

    def save_analysis(
        self,
        fixture_id: int,
        raw_data: Dict[str, Any],
        analyses: Dict[str, BetAnalysisData]
    ) -> MatchContext:
        """
        Save complete match analysis to store

        Args:
            fixture_id: ID of the fixture
            raw_data: Raw data collected from API
            analyses: Analyzed data (8 bet types)

        Returns:
            Created MatchContext
        """
        fixture_info = raw_data.get("fixture", {})

        # Create context
        context = MatchContext(
            fixture_id=fixture_id,
            home_team=fixture_info.get("teams", {}).get("home", {}).get("name", "Unknown"),
            away_team=fixture_info.get("teams", {}).get("away", {}).get("name", "Unknown"),
            league=fixture_info.get("league", {}).get("name", "Unknown"),
            season=fixture_info.get("league", {}).get("season", 2025),
            date=datetime.fromisoformat(fixture_info.get("fixture", {}).get("date", datetime.utcnow().isoformat())),
            status=fixture_info.get("fixture", {}).get("status", {}).get("short", "NS"),
            raw_data=raw_data,
            analyses=analyses,
            metadata=MatchMetadata(
                context_created_at=datetime.utcnow(),
                api_calls_count=raw_data.get("api_calls_count", 0)
            )
        )

        # Save to store
        self.store.save_context(context)

        # Set as current context
        self.current_match_context = context

        logger.info(
            f"Context saved: {context.home_team} vs {context.away_team} "
            f"({context.metadata.api_calls_count} API calls)"
        )

        return context

    def get_current_context(self) -> Optional[MatchContext]:
        """
        Get the current match context (conversation state)

        Returns:
            Current MatchContext or None
        """
        return self.current_match_context

    def clear_current_context(self):
        """Clear the current match context"""
        self.current_match_context = None
        logger.debug("Current context cleared")

    def get_analysis(self, bet_type: str) -> Optional[BetAnalysisData]:
        """
        Get analysis for a specific bet type from current context

        Args:
            bet_type: Type of bet (1x2, goals, shots, etc.)

        Returns:
            BetAnalysisData or None
        """
        if not self.current_match_context:
            logger.warning("No current context to extract analysis from")
            return None

        analysis = self.current_match_context.analyses.get(bet_type)

        if not analysis:
            logger.warning(f"No analysis found for bet type: {bet_type}")

        return analysis

    def get_all_analyses(self) -> Dict[str, BetAnalysisData]:
        """
        Get all analyses from current context

        Returns:
            Dictionary of analyses by bet type
        """
        if not self.current_match_context:
            logger.warning("No current context")
            return {}

        return self.current_match_context.analyses
