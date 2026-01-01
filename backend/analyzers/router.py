"""
Router for global match analysis using analyzers.
"""
from typing import Dict, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.football_api import FootballAPIClient
from backend.config import settings
from backend.core.data_collector import DataCollector
from backend.agents.context_agent import ContextAgent
from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyzers", tags=["Analyzers"])


class GlobalMatchAnalysisRequest(BaseModel):
    fixture_id: int
    force_refresh: bool = False


def get_context_agent() -> ContextAgent:
    """Create a ContextAgent for analyzers endpoint."""
    api_client = FootballAPIClient(
        api_key=settings.FOOTBALL_API_KEY,
        base_url=settings.FOOTBALL_API_BASE_URL,
        redis_url=settings.REDIS_URL,
        enable_cache=settings.ENABLE_REDIS_CACHE,
    )
    collector = DataCollector(api_client)
    if settings.USE_DB_MATCH_STORE:
        return ContextAgent(collector, db_session_factory=SessionLocal)
    return ContextAgent(collector)


@router.post("/analyze")
async def analyze_match_global(
    request: GlobalMatchAnalysisRequest,
    context_agent: ContextAgent = Depends(get_context_agent),
) -> Dict[str, Any]:
    """
    Global match analysis using analyzers (all bet types).
    """
    try:
        context_data = await context_agent.get_match_context(
            request.fixture_id,
            force_refresh=request.force_refresh
        )
        context = context_data["context"]

        analyses_payload = {}
        for bet_type, analysis in context.analyses.items():
            analyses_payload[bet_type] = {
                "indicators": analysis.indicators,
                "coverage_complete": analysis.coverage_complete,
                "data_sources": analysis.data_sources,
            }

        return {
            "fixture_id": context.fixture_id,
            "match": f"{context.home_team} vs {context.away_team}",
            "league": context.league,
            "season": context.season,
            "date": context.date.isoformat() if context.date else None,
            "status": context.status,
            "analyses": analyses_payload,
            "source": context_data.get("source"),
            "api_calls": context_data.get("api_calls"),
        }

    except Exception as exc:
        logger.error("Analyzers global analysis failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
