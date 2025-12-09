"""
Type definitions for context management.
"""

from typing import TypedDict, Literal, Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class ContextType(str, Enum):
    """Types of context."""
    MATCH = "match"
    LEAGUE = "league"


class MatchStatus(str, Enum):
    """Status of a match."""
    LIVE = "live"
    FINISHED = "finished"
    UPCOMING = "upcoming"


class LeagueStatus(str, Enum):
    """Status of a league."""
    PAST = "past"
    CURRENT = "current"
    UPCOMING = "upcoming"


class UserQuestion(TypedDict):
    """A user question in the context."""
    question: str
    intent: str
    timestamp: str
    endpoints_used: List[str]


class Context(TypedDict):
    """Base context structure."""
    context_id: str
    context_type: ContextType
    created_at: str
    updated_at: str
    user_questions: List[UserQuestion]
    context_size: int  # in bytes
    max_context_size: int  # max 10000 bytes


class MatchContext(Context):
    """Context for a match."""
    status: MatchStatus
    fixture_id: int
    match_date: str
    home_team: str
    away_team: str
    league: str
    data_collected: Dict[str, Any]  # Collected API data


class LeagueContext(Context):
    """Context for a league."""
    status: LeagueStatus
    league_id: int
    league_name: str
    country: str
    season: int
    data_collected: Dict[str, Any]  # Collected API data
