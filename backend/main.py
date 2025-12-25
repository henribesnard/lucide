
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uuid
import logging
from datetime import datetime, timedelta

from backend.agents.pipeline import LucidePipeline
from backend.config import settings
from backend.api.football_api import FootballAPIClient
from backend.db.database import init_db, get_db
from backend.auth.router import router as auth_router
from backend.conversations.router import router as conversations_router
from backend.context.context_manager import ContextManager
from backend.context.circuit_breaker import circuit_breaker_manager
from backend.auth.dependencies import get_current_user, get_current_admin_user
from backend.db.models import User, Conversation
from backend.utils.session_manager import session_manager
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session

# Import new types and constants
from backend.types.zones import Zone, ZoneType
from backend.agents.international_competitions import INTERNATIONAL_COMPETITIONS
from backend.constants.favorite_leagues import is_favorite_league

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

# CORS configuration from environment
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
logger.info(f"CORS origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    model_type: Optional[str] = "slow"  # "slow" (DeepSeek, par défaut), "medium" (GPT-4o-mini), "fast" (GPT-4o)


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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat endpoint - REQUIRES AUTHENTICATION.

    Only authenticated users can send messages.
    Session is automatically created/retrieved per user.
    """
    try:
        # Use user_id as session_id for user isolation, or request.session_id if provided
        if request.session_id:
             session_id = request.session_id
        else:
             # Generate a new UUID for the conversation
             session_id = str(uuid.uuid4())

        # Track session in Redis for TTL management
        session_data = await session_manager.get_session(session_id)
        is_new_session = session_data is None

        if not session_data:
            # New session - store metadata in Redis
            await session_manager.set_session(session_id, {
                "user_id": str(current_user.user_id),
                "email": current_user.email,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            })
            logger.info(f"Session {session_id} registered in Redis")
        else:
            # Existing session - update last activity (TTL auto-refreshed by get_session)
            session_data["last_activity"] = datetime.utcnow().isoformat()
            await session_manager.set_session(session_id, session_data)

        # Create Conversation in database if it doesn't exist
        if is_new_session:
            existing_conv = db.query(Conversation).filter(
                Conversation.conversation_id == session_id,
                Conversation.user_id == current_user.user_id
            ).first()

            if not existing_conv:
                # Extract title from first message
                title = request.message[:50] + "..." if len(request.message) > 50 else request.message

                new_conversation = Conversation(
                    conversation_id=session_id,
                    user_id=current_user.user_id,
                    title=title
                )
                db.add(new_conversation)
                db.commit()
                logger.info(f"Created conversation {session_id} in database for user {current_user.email}")

        # Create or get pipeline instance
        if session_id not in sessions:
            logger.info(f"Creating new pipeline for user {current_user.email} (ID: {session_id})")
            sessions[session_id] = LucidePipeline(session_id=session_id)

        pipeline = sessions[session_id]
        message_to_process = request.message
        if request.context:
            logger.info(f"Processing with context: {request.context}")
        logger.info(f"Processing message for session {session_id}: {message_to_process[:120]}...")

        result = await pipeline.process(
            message_to_process,
            context=request.context,
            user_id=str(current_user.user_id),
            model_type=request.model_type or "slow"
        )

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


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream chat responses using Server-Sent Events (SSE).
    Same logic as /chat but returns response progressively.
    """
    import json
    import asyncio

    async def event_generator():
        try:
            # Session management (same as /chat)
            if request.session_id:
                session_id = request.session_id
            else:
                # Generate a new UUID for the conversation
                session_id = str(uuid.uuid4())

            # Track session in Redis for TTL management
            session_data = await session_manager.get_session(session_id)
            is_new_session = session_data is None

            if not session_data:
                # New session - store metadata in Redis
                await session_manager.set_session(session_id, {
                    "user_id": str(current_user.user_id),
                    "email": current_user.email,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat()
                })
                logger.info(f"[STREAM] Session {session_id} registered in Redis")
            else:
                # Existing session - update last activity
                session_data["last_activity"] = datetime.utcnow().isoformat()
                await session_manager.set_session(session_id, session_data)

            # Create Conversation in database if it doesn't exist
            if is_new_session:
                existing_conv = db.query(Conversation).filter(
                    Conversation.conversation_id == session_id,
                    Conversation.user_id == current_user.user_id
                ).first()

                if not existing_conv:
                    # Extract title from first message
                    title = request.message[:50] + "..." if len(request.message) > 50 else request.message

                    new_conversation = Conversation(
                        conversation_id=session_id,
                        user_id=current_user.user_id,
                        title=title
                    )
                    db.add(new_conversation)
                    db.commit()
                    logger.info(f"[STREAM] Created conversation {session_id} in database for user {current_user.email}")

            # Create or get pipeline instance
            if session_id not in sessions:
                logger.info(f"[STREAM] Creating new pipeline for user {current_user.email} (ID: {session_id})")
                sessions[session_id] = LucidePipeline(session_id=session_id)

            pipeline = sessions[session_id]
            message_to_process = request.message

            if request.context:
                logger.info(f"Processing with context: {request.context}")
            logger.info(f"[STREAM] Processing message for session {session_id}: {message_to_process[:120]}...")

            # Send status update
            yield f"data: {json.dumps({'type': 'status', 'message': 'Processing your request...'})}\n\n"

            # Run the pipeline
            result = await pipeline.process(
                message_to_process,
                context=request.context,
                user_id=str(current_user.user_id),
                model_type=request.model_type or "slow"
            )

            intent_obj = result["intent"]
            tool_names = [tool.name for tool in result["tool_results"]]
            full_response = result["answer"]

            # Send metadata
            yield f"data: {json.dumps({'type': 'metadata', 'session_id': session_id, 'intent': intent_obj.intent, 'tools': tool_names})}\n\n"

            # Stream the response in chunks (word by word for smooth experience)
            words = full_response.split()
            chunk_size = 3  # Send 3 words at a time

            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i+chunk_size])
                if i + chunk_size < len(words):
                    chunk += ' '  # Add space if not last chunk

                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming

            # Send completion event
            yield f"data: {json.dumps({'type': 'done', 'message': 'Response complete'})}\n\n"

        except Exception as exc:
            logger.error(f"Error in chat stream endpoint: {exc}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


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

    # Delete from both in-memory and Redis
    session_found = False

    if session_id in sessions:
        await sessions[session_id].close()
        del sessions[session_id]
        session_found = True

    # Delete from Redis
    redis_deleted = await session_manager.delete_session(session_id)
    if redis_deleted:
        session_found = True

    if session_found:
        logger.info(f"Session {session_id} deleted (in-memory + Redis)")
        return {"message": f"Session {session_id} deleted"}

    raise HTTPException(status_code=404, detail="Session not found")


@app.on_event("startup")
async def startup_event():
    global football_client, context_manager
    logger.info("LUCIDE API starting up...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"ENABLE_MULTI_LLM: {settings.ENABLE_MULTI_LLM}")
    logger.info(f"ENABLE_REDIS_CACHE: {settings.ENABLE_REDIS_CACHE}")
    logger.info(f"ENABLE_PARALLEL_API_CALLS: {settings.ENABLE_PARALLEL_API_CALLS}")
    if settings.ENABLE_MULTI_LLM:
        logger.info(f"Slow LLM (default): {settings.SLOW_LLM_PROVIDER}/{settings.SLOW_LLM_MODEL}")
        logger.info(f"Medium LLM: {settings.MEDIUM_LLM_PROVIDER}/{settings.MEDIUM_LLM_MODEL}")
        logger.info(f"Fast LLM: {settings.FAST_LLM_PROVIDER}/{settings.FAST_LLM_MODEL}")

    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Initialize session manager
    try:
        logger.info("Initializing session manager...")
        await session_manager.initialize()
        logger.info("Session manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize session manager: {e}")

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

    # Close all active pipelines
    for _, pipeline in sessions.items():
        await pipeline.close()

    # Close session manager
    await session_manager.close()

    # Close football API client
    if football_client:
        await football_client.close()

    # Close context manager
    if context_manager:
        await context_manager.close()


# ==========================================
# DATA ENDPOINTS FOR FRONTEND
# ==========================================

@app.get("/api/countries", tags=["Data"])
async def get_countries(current_user: User = Depends(get_current_user)):
    """Legacy endpoint: Get all available countries from API-Football."""
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")
        countries = await football_client.get_countries()
        return {"countries": countries}
    except Exception as exc:
        logger.error(f"Error fetching countries: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/zones", tags=["Data"])
async def get_zones(current_user: User = Depends(get_current_user)):
    """
    Récupère toutes les zones disponibles (pays + confédérations).
    Retourne une liste organisée :
    - Pays nationaux (avec ligues domestiques)
    - Confédérations continentales (UEFA, CAF, etc.)
    - Organisation internationale (FIFA)
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        zones = []

        # 1. Récupérer tous les pays depuis l'API-Football
        countries = await football_client.get_countries()

        # Pour optimiser, on pourrait filtrer, mais pour l'instant on retourne tout
        # L'optimisation "pays avec ligues actives" peut être lourde en appels API
        # On va simplifier en retournant tous les pays comme avant, mais typés 'national'
        for country in countries:
            zones.append(Zone(
                code=country["code"],
                name=country["name"],
                zone_type=ZoneType.NATIONAL,
                flag=country["flag"] or "🏳️"
            ).to_dict())

        # 2. Ajouter les confédérations internationales
        for conf_code, conf_data in INTERNATIONAL_COMPETITIONS.items():
            zones.append(Zone(
                code=conf_code,
                name=conf_data["display_name"],
                zone_type=ZoneType.CONTINENTAL if conf_code != "FIFA" else ZoneType.INTERNATIONAL,
                flag=conf_data["flag"]
            ).to_dict())

        return {"zones": zones}

    except Exception as exc:
        logger.error(f"Error fetching zones: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/leagues/all", tags=["Data"])
async def get_all_leagues(
    season: Optional[int] = None,
    current: Optional[bool] = True,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère toutes les ligues disponibles (nationales + internationales).
    Utilise l'API-Football avec type=league et type=cup pour récupérer toutes les compétitions.
    - Ajoute le flag is_favorite sur les ligues connues
    - Tri : favoris en haut, puis par pays/nom
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Saison par défaut (calendrier européen)
        if not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        all_leagues = []
        seen_ids = set()

        logger.info(f"Fetching leagues for season {season}...")

        # 1. Récupérer toutes les ligues (type=league)
        try:
            logger.info("Fetching type=league...")
            leagues_data = await football_client.get_leagues(
                type_="league",
                current=current,
                season=season
            )
            logger.info(f"Found {len(leagues_data)} leagues")

            for league_data in leagues_data:
                league = league_data.get("league", {})
                country_data = league_data.get("country", {})
                league_id = league.get("id")

                if not league_id or league_id in seen_ids:
                    continue

                seen_ids.add(league_id)
                all_leagues.append({
                    "id": league_id,
                    "name": league.get("name"),
                    "country": country_data.get("name", "Unknown"),
                    "country_code": country_data.get("code", ""),
                    "logo": league.get("logo", ""),
                    "flag": country_data.get("flag", ""),
                    "type": league.get("type", "league"),
                    "season": season,
                    "is_favorite": is_favorite_league(int(league_id))
                })
        except Exception as exc:
            logger.error(f"Error fetching leagues: {exc}", exc_info=True)

        # 2. Récupérer toutes les coupes (type=cup)
        try:
            logger.info("Fetching type=cup...")
            cups_data = await football_client.get_leagues(
                type_="cup",
                current=current,
                season=season
            )
            logger.info(f"Found {len(cups_data)} cups")

            for league_data in cups_data:
                league = league_data.get("league", {})
                country_data = league_data.get("country", {})
                league_id = league.get("id")

                if not league_id or league_id in seen_ids:
                    continue

                seen_ids.add(league_id)
                all_leagues.append({
                    "id": league_id,
                    "name": league.get("name"),
                    "country": country_data.get("name", "World"),
                    "country_code": country_data.get("code", "WORLD"),
                    "logo": league.get("logo", ""),
                    "flag": country_data.get("flag", "🏆"),
                    "type": league.get("type", "cup"),
                    "season": season,
                    "is_favorite": is_favorite_league(int(league_id))
                })
        except Exception as exc:
            logger.error(f"Error fetching cups: {exc}", exc_info=True)

        logger.info(f"Total leagues collected: {len(all_leagues)}")

        # 3. Filtrage recherche
        if search:
            search_lower = search.lower()
            all_leagues = [
                l for l in all_leagues
                if (l.get("name") and search_lower in l["name"].lower()) or
                   (l.get("country") and search_lower in l["country"].lower())
            ]

        # 4. Tri : favoris en haut puis pays/nom
        favorites_first = []
        non_favorites = []
        for league in all_leagues:
            (favorites_first if league.get("is_favorite") else non_favorites).append(league)

        favorites_first.sort(key=lambda l: l.get("name", ""))
        non_favorites.sort(key=lambda l: (l.get("country", ""), l.get("name", "")))
        ordered = favorites_first + non_favorites

        logger.info(f"Returning {len(ordered)} leagues ({len(favorites_first)} favorites)")

        return {
            "leagues": ordered,
            "total": len(ordered),
            "season": season
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching all leagues: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/leagues", tags=["Data"])
async def get_leagues(
    country: Optional[str] = None, # Legacy query param
    zone_code: Optional[str] = None, # New query param
    current: Optional[bool] = True,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les ligues pour une zone donnée.
    Supporte 'country' (compatibilité) et 'zone_code' (nouveau).
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Determine effective zone/country
        effective_zone = zone_code if zone_code else country
        
        # Get current season
        current_year = datetime.now().year
        season = current_year if datetime.now().month >= 8 else current_year - 1

        # Cas 1 : Zone nationale (pays) ou non spécifiée
        # Si code 2 lettres ou country param
        if effective_zone and len(effective_zone) == 2:
            leagues = await football_client.get_leagues(
                country=effective_zone if not zone_code else None, 
                code=effective_zone if zone_code else None, 
                current=current,
                season=season 
            )
            # API football sometimes needs country name, sometimes code. 
            # If zone_code is passed (like "FR"), use code. If country name (like "France"), use country.
            # But wait, logic above is a bit complex. Let's simplify.
            # get_leagues supports 'country' (name) or 'code'.
            
            # If using new system, effective_zone is likley a code (FR, GB).
            # If using old system, country is a name (France).
            
            # Let's try to pass whatever we have.
            return {"leagues": leagues, "zone_type": "national"}

        # Cas 2 : Zone continentale/internationale (UEFA, CAF...)
        elif effective_zone in INTERNATIONAL_COMPETITIONS:
            confederation = INTERNATIONAL_COMPETITIONS[effective_zone]
            competition_ids = [comp["id"] for comp in confederation["competitions"]]

            # Récupérer les détails de chaque compétition
            leagues = []
            for comp_id in competition_ids:
                league_data = await football_client.get_leagues(league_id=comp_id, current=current, season=season)
                if league_data:
                    leagues.extend(league_data)

            return {"leagues": leagues, "zone_type": confederation["display_name"]}

        # Cas 3 : Default / All (legacy behavior or fallback)
        else:
             # If country was passed but didn't match 2 chars and wasn't in COMPs, maybe it's full name like "France"
             # Try standard fetch
            leagues = await football_client.get_leagues(
                country=country if country else None,
                current=current,
                season=season
            )
            return {"leagues": leagues, "zone_type": "all"}

    except Exception as exc:
        logger.error(f"Error fetching leagues: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/fixtures", tags=["Data"])
async def get_fixtures(
    league_id: Optional[int] = None,
    date: Optional[str] = None,  # Format: YYYY-MM-DD
    from_date: Optional[str] = None,  # Pour plage de dates
    to_date: Optional[str] = None,
    season: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Récupère les fixtures pour une ligue et une date/période donnée.
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Valeurs par défaut
        if not date and not from_date:
            date = datetime.now().strftime("%Y-%m-%d")

        if not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        fixtures = []
        eff_from = None
        eff_to = None

        # Cas 1 : Date spécifique
        if date and not from_date:
            fixtures = await football_client.get_fixtures(
                league_id=league_id,
                date=date,
                season=season
            )

        # Cas 2 : Plage de dates
        elif from_date and to_date:
            eff_from = from_date
            eff_to = to_date
            fixtures = await football_client.get_fixtures(
                league_id=league_id,
                from_date=from_date,
                to_date=to_date,
                season=season
            )

        # Cas 3 : Date + plage (ex: implicite dans le backend si on voulait, mais ici on gère date unique ou plage)
        # La spec mentionne "target_date +- 3 jours" logic in backend if needed.
        # But let's stick to what parameters provide. 
        # API Football has specific params.
        
        # Trier par timestamp
        fixtures_sorted = sorted(
            fixtures,
            key=lambda f: f.get("fixture", {}).get("timestamp", 0)
        )

        return {
            "fixtures": fixtures_sorted,
            "date": date,
            "from_date": eff_from,
            "to_date": eff_to,
            "total": len(fixtures_sorted)
        }
    except Exception as exc:
        logger.error(f"Error fetching fixtures: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/teams", tags=["Data"])
async def get_teams(
    league: Optional[int] = None,
    league_id: Optional[int] = None,
    season: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get teams, optionally filtered by league/season or search.
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        effective_league = league_id or league
        if not effective_league and not search:
            return {"teams": [], "total": 0}

        if effective_league and not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        teams = await football_client.get_teams(
            league_id=effective_league,
            season=season,
            search=search,
        )

        mapped = []
        for item in teams:
            team = item.get("team", item) or {}
            mapped.append({
                "id": team.get("id"),
                "name": team.get("name"),
                "code": team.get("code"),
                "country": team.get("country"),
                "founded": team.get("founded"),
                "logo": team.get("logo"),
                "national": team.get("national", False),
            })

        return {"teams": mapped, "total": len(mapped)}
    except Exception as exc:
        logger.error(f"Error fetching teams: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/players", tags=["Data"])
async def get_players(
    team: Optional[int] = None,
    league: Optional[int] = None,
    season: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    current_user: User = Depends(get_current_user)
):
    """
    Get players, optionally filtered by team/league/season or search.
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        if not team and not league and not search:
            return {"players": [], "total": 0}

        if not season:
            current_year = datetime.now().year
            season = current_year if datetime.now().month >= 8 else current_year - 1

        data = await football_client.get_players(
            team_id=team,
            league_id=league,
            season=season,
            search=search,
            page=page,
        )

        players = data.get("response", [])
        mapped = []
        for item in players:
            player = item.get("player", {}) or {}
            birth = player.get("birth") or {}
            stats = (item.get("statistics") or [{}])[0] or {}
            games = stats.get("games") or {}
            mapped.append({
                "id": player.get("id"),
                "name": player.get("name"),
                "firstname": player.get("firstname"),
                "lastname": player.get("lastname"),
                "age": player.get("age"),
                "birth": {
                    "date": birth.get("date") or "",
                    "place": birth.get("place") or "",
                    "country": birth.get("country") or "",
                },
                "nationality": player.get("nationality") or "",
                "height": player.get("height") or "",
                "weight": player.get("weight") or "",
                "position": player.get("position") or games.get("position") or "",
                "photo": player.get("photo") or "",
                "injured": player.get("injured", False),
            })

        return {
            "players": mapped,
            "total": len(mapped),
            "paging": data.get("paging") or {},
        }
    except Exception as exc:
        logger.error(f"Error fetching players: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/fixtures/{fixture_id}/players", tags=["Data"])
async def get_fixture_players(
    fixture_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get players from both teams of a match (for player dropdown in match mode).
    Returns players grouped by home/away teams.
    """
    try:
        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Get fixture details to extract team IDs
        fixtures = await football_client.get_fixtures(fixture_id=fixture_id)

        if not fixtures or len(fixtures) == 0:
            raise HTTPException(status_code=404, detail=f"Fixture {fixture_id} not found")

        fixture = fixtures[0]
        teams_data = fixture.get("teams", {})
        home_team = teams_data.get("home", {})
        away_team = teams_data.get("away", {})

        home_team_id = home_team.get("id")
        away_team_id = away_team.get("id")

        if not home_team_id or not away_team_id:
            raise HTTPException(status_code=500, detail="Could not extract team IDs from fixture")

        # Get squads for both teams
        home_squad_data = await football_client.get_players_squads(team_id=home_team_id)
        away_squad_data = await football_client.get_players_squads(team_id=away_team_id)

        # Helper function to map squad data to player format
        def map_squad_to_players(squad_data, team_info):
            if not squad_data or len(squad_data) == 0:
                return []

            squad_item = squad_data[0]
            players_list = squad_item.get("players", [])

            mapped = []
            for p in players_list:
                mapped.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "firstname": p.get("name", "").split()[0] if p.get("name") else "",
                    "lastname": " ".join(p.get("name", "").split()[1:]) if p.get("name") else "",
                    "age": p.get("age"),
                    "photo": p.get("photo") or "",
                    "position": p.get("position") or "",
                    "number": p.get("number"),
                    "nationality": "",
                    "birth": {"date": "", "place": "", "country": ""},
                    "height": "",
                    "weight": "",
                    "injured": False,
                })
            return mapped

        home_players = map_squad_to_players(home_squad_data, home_team)
        away_players = map_squad_to_players(away_squad_data, away_team)

        return {
            "fixture_id": fixture_id,
            "teams": {
                "home": {
                    "team": {
                        "id": home_team_id,
                        "name": home_team.get("name"),
                        "logo": home_team.get("logo"),
                    },
                    "players": home_players
                },
                "away": {
                    "team": {
                        "id": away_team_id,
                        "name": away_team.get("name"),
                        "logo": away_team.get("logo"),
                    },
                    "players": away_players
                }
            }
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching fixture players: {exc}", exc_info=True)
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


@app.get("/api/context/team/{team_id}", tags=["Context"])
async def get_team_context(
    team_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get or create context for a specific team."""
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Try to get existing context
        context_id = f"team_{team_id}"
        context = await context_manager.get_context(context_id)

        if context:
            logger.info(f"Found existing context for team {team_id}")
            return {"context": context}

        # Create new context - fetch team data
        logger.info(f"Creating new context for team {team_id}")
        teams = await football_client.get_teams(team_id=team_id)

        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")

        team_entry = teams[0] or {}
        team_data = team_entry.get("team", team_entry)

        context = context_manager.create_team_context(
            team_id=team_id,
            team_name=team_data.get("name") or "",
            team_code=team_data.get("code") or "",
            country=team_data.get("country") or "",
            founded=team_data.get("founded") or 0,
            logo=team_data.get("logo") or "",
        )

        # Save to Redis
        await context_manager.save_context(context)

        return {"context": context}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching team context: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/context/league/{league_id}/team/{team_id}", tags=["Context"])
async def get_league_team_context(
    league_id: int,
    team_id: int,
    season: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get or create context for a team in a specific league."""
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
        context_id = f"league_{league_id}_team_{team_id}_{season}"
        context = await context_manager.get_context(context_id)

        if context:
            logger.info(f"Found existing context for team {team_id} in league {league_id}")
            return {"context": context}

        # Create new context - fetch team and league data
        logger.info(f"Creating new context for team {team_id} in league {league_id}")

        teams = await football_client.get_teams(team_id=team_id)
        if not teams:
            raise HTTPException(status_code=404, detail="Team not found")
        team_entry = teams[0] or {}
        team_data = team_entry.get("team", team_entry)

        leagues = await football_client.get_leagues(league_id=league_id, season=season)
        if not leagues:
            raise HTTPException(status_code=404, detail="League not found")
        league_entry = leagues[0] or {}
        league_data = league_entry.get("league", league_entry)

        context = context_manager.create_league_team_context(
            team_id=team_id,
            team_name=team_data.get("name") or "",
            team_code=team_data.get("code") or "",
            league_id=league_id,
            league_name=league_data.get("name") or "",
            season=season,
        )

        # Save to Redis
        await context_manager.save_context(context)

        return {"context": context}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching league-team context: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/context/player/{player_id}", tags=["Context"])
async def get_player_context(
    player_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get or create context for a specific player."""
    try:
        if not context_manager:
            raise HTTPException(status_code=500, detail="Context manager not initialized")

        if not football_client:
            raise HTTPException(status_code=500, detail="Football API client not initialized")

        # Try to get existing context
        context_id = f"player_{player_id}"
        context = await context_manager.get_context(context_id)

        if context:
            logger.info(f"Found existing context for player {player_id}")
            return {"context": context}

        # Create new context - fetch player data
        logger.info(f"Creating new context for player {player_id}")
        players = await football_client.get_player_profile(player_id=player_id)

        if not players:
            raise HTTPException(status_code=404, detail="Player not found")

        player_entry = players[0] or {}
        player_data = player_entry.get("player", player_entry)
        stats_block = player_entry.get("statistics") or []
        team_block = stats_block[0].get("team") if stats_block else {}
        current_team = team_block.get("name") if team_block else None
        current_team_id = team_block.get("id") if team_block else None

        context = context_manager.create_player_context(
            player_id=player_id,
            player_name=player_data.get("name") or "",
            firstname=player_data.get("firstname") or "",
            lastname=player_data.get("lastname") or "",
            age=player_data.get("age") or 0,
            nationality=player_data.get("nationality") or "",
            position=player_data.get("position") or "Unknown",
            photo=player_data.get("photo") or "",
            current_team=current_team,
            current_team_id=current_team_id,
            injured=bool(player_data.get("injured", False)),
        )

        # Save to Redis
        await context_manager.save_context(context)

        return {"context": context}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error fetching player context: {exc}", exc_info=True)
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
        league_team_contexts = [
            cid for cid in context_ids if cid.startswith("league_") and "_team_" in cid
        ]
        league_contexts = [
            cid for cid in context_ids if cid.startswith("league_") and "_team_" not in cid
        ]
        team_contexts = [cid for cid in context_ids if cid.startswith("team_")]
        player_contexts = [cid for cid in context_ids if cid.startswith("player_")]

        stats["by_type"] = {
            "match": len(match_contexts),
            "league": len(league_contexts),
            "league_team": len(league_team_contexts),
            "team": len(team_contexts),
            "player": len(player_contexts)
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
