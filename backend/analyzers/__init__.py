"""
Analyzers module - 8 bet type analyzers
"""
from backend.analyzers.base_analyzer import BaseAnalyzer
from backend.analyzers.bet_1x2_analyzer import Bet1X2Analyzer
from backend.analyzers.bet_goals_analyzer import BetGoalsAnalyzer
from backend.analyzers.bet_shots_analyzer import BetShotsAnalyzer
from backend.analyzers.bet_corners_analyzer import BetCornersAnalyzer
from backend.analyzers.bet_cards_team_analyzer import BetCardsTeamAnalyzer
from backend.analyzers.bet_card_player_analyzer import BetCardPlayerAnalyzer
from backend.analyzers.bet_scorer_analyzer import BetScorerAnalyzer
from backend.analyzers.bet_assister_analyzer import BetAssisterAnalyzer

__all__ = [
    "BaseAnalyzer",
    "Bet1X2Analyzer",
    "BetGoalsAnalyzer",
    "BetShotsAnalyzer",
    "BetCornersAnalyzer",
    "BetCardsTeamAnalyzer",
    "BetCardPlayerAnalyzer",
    "BetScorerAnalyzer",
    "BetAssisterAnalyzer"
]
