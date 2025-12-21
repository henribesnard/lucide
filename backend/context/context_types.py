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
    TEAM = "team"
    PLAYER = "player"
    LEAGUE_TEAM = "league_team"


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


class TeamStatus(str, Enum):
    """Status of a team."""
    ACTIVE = "active"
    INACTIVE = "inactive"


class PlayerStatus(str, Enum):
    """Status of a player."""
    ACTIVE = "active"
    INJURED = "injured"
    TRANSFERRED = "transferred"
    RETIRED = "retired"


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


class TeamContext(Context):
    """Context for a team (all competitions)."""
    status: TeamStatus
    team_id: int
    team_name: str
    team_code: str
    country: str
    founded: int
    logo: str
    data_collected: Dict[str, Any]  # Collected API data


class LeagueTeamContext(Context):
    """Context for a team in a specific league."""
    status: TeamStatus
    team_id: int
    team_name: str
    team_code: str
    league_id: int
    league_name: str
    season: int
    data_collected: Dict[str, Any]  # Collected API data


class PlayerContext(Context):
    """Context for a player."""
    status: PlayerStatus
    player_id: int
    player_name: str
    firstname: str
    lastname: str
    age: int
    nationality: str
    position: str
    current_team: Optional[str]
    current_team_id: Optional[int]
    photo: str
    data_collected: Dict[str, Any]  # Collected API data
