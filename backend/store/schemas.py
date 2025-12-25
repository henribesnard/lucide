"""
Pydantic schemas for match context storage
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TeamInfo(BaseModel):
    """Information about a team"""
    id: int
    name: str
    logo: Optional[str] = None


class FixtureInfo(BaseModel):
    """Information about a fixture"""
    fixture_id: int
    date: datetime
    status: str
    home: TeamInfo
    away: TeamInfo
    league_id: int
    league_name: str
    season: int
    venue: Optional[str] = None


class BetAnalysisData(BaseModel):
    """Analysis data for a specific bet type"""
    indicators: Dict[str, Any] = Field(default_factory=dict)
    data_sources: List[str] = Field(default_factory=list)
    coverage_complete: bool = False


class MatchMetadata(BaseModel):
    """Metadata about the match context"""
    version: str = "2.0"
    context_created_at: datetime
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    api_calls_count: int = 0


class MatchContext(BaseModel):
    """Complete context for a match analysis"""
    # Match identification
    fixture_id: int
    home_team: str
    away_team: str
    league: str
    season: int
    date: datetime
    status: str

    # Raw data from API
    raw_data: Dict[str, Any] = Field(default_factory=dict)

    # Analyzed data (8 bet types)
    analyses: Dict[str, BetAnalysisData] = Field(default_factory=dict)

    # Metadata
    metadata: MatchMetadata

    # Causal cache (lightweight metrics/findings)
    causal_metrics: Dict[str, Any] = Field(default_factory=dict)
    causal_findings: List[Dict[str, Any]] = Field(default_factory=list)
    causal_confidence: Optional[str] = None
    causal_version: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
