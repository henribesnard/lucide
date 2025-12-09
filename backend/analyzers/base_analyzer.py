"""
Base Analyzer - Abstract class for all bet type analyzers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

from backend.store.schemas import BetAnalysisData

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers

    Each analyzer is responsible for:
    - Defining required data sources
    - Calculating indicators for a specific bet type
    - Checking data coverage
    """

    @property
    @abstractmethod
    def bet_type(self) -> str:
        """Type of bet analyzed (1x2, goals, shots, etc.)"""
        pass

    @property
    @abstractmethod
    def required_sources(self) -> List[str]:
        """
        List of required data sources

        Possible sources:
        - predictions
        - h2h_history
        - h2h_details
        - standings
        - team1_stats / team2_stats
        - injuries
        - top_scorers
        - top_assists
        - top_yellow / top_red
        """
        pass

    @abstractmethod
    def calculate_indicators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate indicators specific to this bet type

        Args:
            raw_data: Raw data collected from API

        Returns:
            Dictionary of calculated indicators
        """
        pass

    def analyze(self, raw_data: Dict[str, Any]) -> BetAnalysisData:
        """
        Main analysis method

        Args:
            raw_data: Raw data from API collection

        Returns:
            BetAnalysisData with indicators and metadata
        """
        logger.debug(f"Analyzing {self.bet_type}")

        # Calculate indicators
        indicators = self.calculate_indicators(raw_data)

        # Determine available sources
        sources_used = self._get_available_sources(raw_data)

        # Check coverage
        coverage_complete = self._check_coverage(sources_used)

        return BetAnalysisData(
            indicators=indicators,
            data_sources=sources_used,
            coverage_complete=coverage_complete
        )

    def _get_available_sources(self, raw_data: Dict[str, Any]) -> List[str]:
        """Identify which data sources are available"""
        sources = []

        if raw_data.get("predictions"):
            sources.append("predictions")
        if raw_data.get("h2h_history"):
            sources.append("h2h_history")
        if raw_data.get("h2h_details"):
            sources.append("h2h_details")
        if raw_data.get("standings"):
            sources.append("standings")
        if raw_data.get("team1_stats") or raw_data.get("team2_stats"):
            sources.append("team_statistics")
        if raw_data.get("injuries"):
            sources.append("injuries")
        if raw_data.get("top_scorers"):
            sources.append("top_scorers")
        if raw_data.get("top_assists"):
            sources.append("top_assists")
        if raw_data.get("top_yellow") or raw_data.get("top_red"):
            sources.append("top_cards")

        return sources

    def _check_coverage(self, available_sources: List[str]) -> bool:
        """Check if all required sources are available"""
        for required in self.required_sources:
            if required not in available_sources:
                logger.warning(
                    f"[{self.bet_type}] Missing required source: {required}"
                )
                return False
        return True

    def _safe_get(self, data: Any, *keys, default=None):
        """Safely get nested dict value"""
        try:
            result = data
            for key in keys:
                if isinstance(result, dict):
                    result = result.get(key)
                else:
                    return default
                if result is None:
                    return default
            return result
        except (KeyError, TypeError, AttributeError):
            return default
