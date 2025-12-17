from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid
import logging
from datetime import datetime

from backend.agents.pipeline import LucidePipeline
from backend.config import settings
from backend.api.football_api import FootballAPIClient
from backend.db.database import init_db
from backend.auth.router import router as auth_router
from backend.conversations.router import router as conversations_router
from backend.context.context_manager import ContextManager
from backend.context.circuit_breaker import circuit_breaker_manager
from backend.auth.dependencies import get_current_user, get_current_admin_user
from backend.db.models import User
from fastapi import FastAPI, HTTPException, Depends, status

# Logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LUCIDE API",
    description="Assistant intelligent d'analyse football",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(conversations_router)

sessions: Dict[str, LucidePipeline] = {}
football_client: Optional[FootballAPIClient] = None
context_manager: Optional[ContextManager] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    intent: str
    entities: Dict[str, Any]
    tools: List[str]


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "LUCIDE API",
        "version": "2.0.0",
        "description": "Assistant football propulse par DeepSeek function calling",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health():
    return HealthResponse(
        status="ok",
        llm_provider=settings.LLM_PROVIDER,
        llm_model=settings.DEEPSEEK_MODEL if settings.LLM_PROVIDER == "deepseek" else settings.OPENAI_MODEL,
    )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat endpoint - REQUIRES AUTHENTICATION.

    Only authenticated users can send messages.
    Session is automatically created/retrieved per user.
    """
    try:
        # Use user_id as session_id for user isolation, or request.session_id if provided (for multi-session per user possibility in future)
        # For now, let's stick to strict user isolation if session_id is not provided
        if request.session_id:
             # TODO: specific check if user owns this session_id if we store session ownership
             session_id = request.session_id
        else:
             session_id = f"user_{current_user.user_id}"

        if session_id not in sessions:
            logger.info(f"Creating new session for user {current_user.email} (ID: {session_id})")
            sessions[session_id] = LucidePipeline(
                session_id=session_id,
                user_id=current_user.user_id # Pass user_id for context in pipeline
            )

        pipeline = sessions[session_id]
        message_to_process = request.message
        if request.context:
            logger.info(f"Processing with context: {request.context}")
        logger.info(f"Processing message for session {session_id}: {message_to_process[:120]}...")
        
        # We need to ensure the pipeline process method accepts user_id if we want to pass it down further
        # Assuming pipeline.process signature handles it or we pass it via context
        result = await pipeline.process(message_to_process, user_id=current_user.user_id)

        intent_obj = result["intent"]
        tool_names = [tool.name for tool in result["tool_results"]]

        return ChatResponse(
            response=result["answer"],
            session_id=session_id,
            intent=intent_obj.intent,
            entities=intent_obj.entities,
            tools=tool_names,
        )

    except Exception as exc:
        logger.error(f"Error in chat endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a session - Only owner can delete."""
    
    # Simple ownership check logic for now: 
    # If session_id starts with "user_", it must match the current user
    if session_id.startswith("user_"):
        expected_session_id = f"user_{current_user.user_id}"
        if session_id != expected_session_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete another user's session"
            )

    if session_id in sessions:
        # TODO: Real implementation should verify if generic session_id belongs to user
        await sessions[session_id].close()
        del sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.on_event("startup")
async def startup_event():
    global football_client, context_manager
    logger.info("LUCIDE API starting up...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")

    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    football_client = FootballAPIClient(api_key=settings.FOOTBALL_API_KEY)

    # Initialize context manager
    try:
        logger.info("Initializing context manager...")
        context_manager = ContextManager()
        logger.info("Context manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize context manager: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    global football_client, context_manager
    logger.info("LUCIDE API shutting down...")
    for _, pipeline in sessions.items():
        await pipeline.close()
    if football_client:
        await football_client.close()
    if context_manager:
        await context_manager.close()


# ==========================================
# DATA ENDPOINTS FOR FRONTEND
# ==========================================

@app.get("/api/countries", tags=["Data"])
async def get_countries(current_user: User = Depends(get_current_user)):
    """Get all available countries from API-Football."""
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")
        countries = await football_client.get_countries()
        return {"countries": countries}
    except Exception as exc:
        logger.error(f"Error fetching countries: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/leagues", tags=["Data"])
async def get_leagues(
    country: Optional[str] = None, 
    current: Optional[bool] = True,
    current_user: User = Depends(get_current_user)
):
    """Get all available leagues, optionally filtered by country."""
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Get current season
        current_year = datetime.now().year
        season = current_year if datetime.now().month >= 8 else current_year - 1

        leagues = await football_client.get_leagues(
            country=country,
            current=current,
            season=season
        )
        return {"leagues": leagues}
    except Exception as exc:
        logger.error(f"Error fetching leagues: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/fixtures", tags=["Data"])
async def get_fixtures(
    league_id: Optional[int] = None,
    date: Optional[str] = None,
    season: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get fixtures for a specific league and date."""
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # If no date provided, use today
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # If no season provided, calculate current season
        if not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        fixtures = await football_client.get_fixtures(
            league_id=league_id,
            date=date,
            season=season
        )
        return {"fixtures": fixtures, "date": date}
    except Exception as exc:
        logger.error(f"Error fetching fixtures: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ==========================================
# CONTEXT ENDPOINTS
# ==========================================

@app.get("/api/context/match/{fixture_id}", tags=["Context"])
async def get_match_context(
    fixture_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get or create context for a specific match."""
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Try to get existing context
        today = datetime.now().strftime("%Y%m%d")
        context_id = f"match_{fixture_id}_{today}"
        context = await context_manager.get_context(context_id)

        if context:
            logger.info(f"Found existing context for match {fixture_id}")
            return {"context": context}

        # Create new context - fetch match data
        logger.info(f"Creating new context for match {fixture_id}")
        fixtures = await football_client.get_fixtures(fixture_id=fixture_id)

        if not fixtures or len(fixtures) == 0:
            raise HTTPException(status_code=404, detail="Match not found")

        fixture = fixtures[0]
        context = context_manager.create_match_context(
            fixture_id=fixture_id,
            match_date=fixture["fixture"]["date"],
            home_team=fixture["teams"]["home"]["name"],
            away_team=fixture["teams"]["away"]["name"],
            league=fixture["league"]["name"],
            status_code=fixture["fixture"]["status"]["short"],
        )

        # Save to Redis
        await context_manager.save_context(context)

        return {"context": context}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching match context: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/context/league/{league_id}", tags=["Context"])
async def get_league_context(
    league_id: int, 
    season: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get or create context for a specific league."""
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Calculate season if not provided
        if not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        # Try to get existing context
        context_id = f"league_{league_id}_{season}"
        context = await context_manager.get_context(context_id)

        if context:
            logger.info(f"Found existing context for league {league_id}")
            return {"context": context}

        # Create new context - fetch league data
        logger.info(f"Creating new context for league {league_id}")
        leagues = await football_client.get_leagues(league_id=league_id, season=season)

        if not leagues or len(leagues) == 0:
            raise HTTPException(status_code=404, detail="League not found")

        league = leagues[0]
        context = context_manager.create_league_context(
            league_id=league_id,
            league_name=league["league"]["name"],
            country=league["country"]["name"],
            season=season,
        )

        # Save to Redis
        await context_manager.save_context(context)

        return {"context": context}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching league context: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/contexts", tags=["Context"])
async def list_contexts(current_user: User = Depends(get_current_user)):
    """List all active contexts."""
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        context_ids = await context_manager.list_active_contexts()
        return {"contexts": context_ids, "count": len(context_ids)}
    except Exception as exc:
        logger.error(f"Error listing contexts: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# MONITORING & HEALTH ENDPOINTS
# ============================================================================

@app.get("/api/health", tags=["Monitoring"])
async def health_check():
    """
    Health check endpoint.

    Returns system health status including context manager and circuit breakers.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "context_manager": "healthy" if context_manager else "unavailable",
                "football_api": "healthy" if football_client else "unavailable"
            }
        }

        # Check circuit breakers
        circuit_states = circuit_breaker_manager.get_all_states()
        unhealthy_circuits = [
            name for name, state in circuit_states.items()
            if state["state"] == "open"
        ]

        if unhealthy_circuits:
            health_status["status"] = "degraded"
            health_status["warnings"] = {
                "circuit_breakers_open": unhealthy_circuits
            }

        return health_status

    except Exception as exc:
        logger.error(f"Health check failed: {exc}", exc_info=True)
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc)
        }


@app.get("/api/circuit-breakers", tags=["Monitoring"])
async def get_circuit_breakers(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get status of all circuit breakers.

    Returns detailed state of all active circuit breakers.
    """
    try:
        states = circuit_breaker_manager.get_all_states()

        # Add summary
        summary = {
            "total": len(states),
            "closed": sum(1 for s in states.values() if s["state"] == "closed"),
            "open": sum(1 for s in states.values() if s["state"] == "open"),
            "half_open": sum(1 for s in states.values() if s["state"] == "half_open")
        }

        return {
            "circuit_breakers": states,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error getting circuit breakers: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/circuit-breakers/reset", tags=["Monitoring"])
async def reset_circuit_breakers(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Reset all circuit breakers (admin only).

    WARNING: This should only be used for testing or emergency situations.
    """
    try:
        circuit_breaker_manager.reset_all()
        logger.warning(f"All circuit breakers have been reset via API by {current_user.email}")

        return {
            "status": "success",
            "message": "All circuit breakers have been reset",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error resetting circuit breakers: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/context/stats", tags=["Monitoring"])
async def get_context_stats(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get context system statistics.

    Returns metrics about context usage, cache hits, etc.
    """
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        context_ids = await context_manager.list_active_contexts()

        # Basic stats
        stats = {
            "total_contexts": len(context_ids),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Count by type
        match_contexts = [cid for cid in context_ids if cid.startswith("match_")]
        league_contexts = [cid for cid in context_ids if cid.startswith("league_")]

        stats["by_type"] = {
            "match": len(match_contexts),
            "league": len(league_contexts)
        }

        return stats

    except Exception as exc:
        logger.error(f"Error getting context stats: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# LOCK MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/locks", tags=["Monitoring"])
async def get_all_locks(
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get all active distributed locks.

    Returns a list of all currently held locks with their details.
    """
    try:
        if not context_manager or not context_manager.lock_manager:
            raise HTTPException(status_code=500, detail="Lock manager not initialized")

        locks = await context_manager.lock_manager.get_all_locks()

        return {
            "locks": locks,
            "count": len(locks),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error getting locks: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/locks/{resource}", tags=["Monitoring"])
async def get_lock_info(
    resource: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Get information about a specific lock.

    Args:
        resource: The resource name (e.g., 'context:match_123_20251209')
    """
    try:
        if not context_manager or not context_manager.lock_manager:
            raise HTTPException(status_code=500, detail="Lock manager not initialized")

        lock_info = await context_manager.lock_manager.get_lock_info(resource)

        if not lock_info:
            raise HTTPException(status_code=404, detail=f"Lock '{resource}' not found")

        return lock_info

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting lock info: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/api/locks/{resource}", tags=["Monitoring"])
async def force_release_lock(
    resource: str,
    current_user: User = Depends(get_current_admin_user)
):
    """
    Force release a lock (admin only).

    WARNING: This should only be used in case of deadlock or emergency.

    Args:
        resource: The resource name to unlock
    """
    try:
        if not context_manager or not context_manager.lock_manager:
            raise HTTPException(status_code=500, detail="Lock manager not initialized")

        released = await context_manager.lock_manager.force_release(resource)

        if released:
            logger.warning(f"Lock forcibly released via API: {resource} by {current_user.email}")
            return {
                "status": "success",
                "message": f"Lock '{resource}' has been forcibly released",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"Lock '{resource}' not found")

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error releasing lock: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
