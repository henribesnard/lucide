"""
Service d'analyse de match - Detection d'assets caches.

Ce service implemente l'algorithme d'analyse de match decrit dans
documentation/ALGORITHME_ANALYSE_MATCH_API_FOOTBALL.md
"""

from .service import MatchAnalysisService
from .types import (
    MatchAnalysisInput,
    MatchAnalysisResult,
    HiddenAsset,
    FeatureSet,
    Pattern,
)

__all__ = [
    "MatchAnalysisService",
    "MatchAnalysisInput",
    "MatchAnalysisResult",
    "HiddenAsset",
    "FeatureSet",
    "Pattern",
]
