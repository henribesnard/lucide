"""
Context manager for Lucide.
Handles context creation, enrichment, storage, and retrieval.
"""

from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime
import sys
import redis

from backend.context.context_types import (
    Context,
    MatchContext,
    LeagueContext,
    MatchStatus,
    LeagueStatus,
    ContextType,
    UserQuestion,
)
from backend.context.status_classifier import StatusClassifier
from backend.context.intent_classifier import IntentClassifier
from backend.context.endpoint_selector import EndpointSelector
from backend.config import settings

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context lifecycle: creation, enrichment, storage, and retrieval."""

    # Max context size in bytes (10KB)
    MAX_CONTEXT_SIZE = 10000

    # Context TTL in Redis (1 hour for active contexts)
    CONTEXT_TTL = 3600

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the context manager.

        Args:
            redis_url: Optional Redis connection URL. If not provided, uses settings.REDIS_URL
        """
        redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    async def close(self):
        """Close the Redis connection."""
        if self.redis_client:
            self.redis_client.close()

    def create_match_context(
        self,
        fixture_id: int,
        match_date: str,
        home_team: str,
        away_team: str,
        league: str,
        status_code: str,
    ) -> MatchContext:
        """
        Create a new match context.

        Args:
            fixture_id: The fixture ID
            match_date: The match date in ISO format
            home_team: Home team name
            away_team: Away team name
            league: League name
            status_code: API-Football status code

        Returns:
            MatchContext dict
        """
        status = StatusClassifier.classify_match_status(status_code, match_date)
        context_id = f"match_{fixture_id}_{datetime.now().strftime('%Y%m%d')}"

        context: MatchContext = {
            "context_id": context_id,
            "context_type": ContextType.MATCH,
            "status": status,
            "fixture_id": fixture_id,
            "match_date": match_date,
            "home_team": home_team,
            "away_team": away_team,
            "league": league,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_questions": [],
            "data_collected": {},
            "context_size": 0,
            "max_context_size": self.MAX_CONTEXT_SIZE,
        }

        # Calculate initial size
        context["context_size"] = sys.getsizeof(json.dumps(context))

        return context

    def create_league_context(
        self,
        league_id: int,
        league_name: str,
        country: str,
        season: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> LeagueContext:
        """
        Create a new league context.

        Args:
            league_id: The league ID
            league_name: League name
            country: Country name
            season: Season year
            start_date: Optional season start date
            end_date: Optional season end date

        Returns:
            LeagueContext dict
        """
        status = StatusClassifier.classify_league_status(season, start_date, end_date)
        context_id = f"league_{league_id}_{season}"

        context: LeagueContext = {
            "context_id": context_id,
            "context_type": ContextType.LEAGUE,
            "status": status,
            "league_id": league_id,
            "league_name": league_name,
            "country": country,
            "season": season,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_questions": [],
            "data_collected": {},
            "context_size": 0,
            "max_context_size": self.MAX_CONTEXT_SIZE,
        }

        # Calculate initial size
        context["context_size"] = sys.getsizeof(json.dumps(context))

        return context

    def enrich_context(
        self,
        context: Context,
        question: str,
        intent: str,
        endpoints_used: List[str],
        api_data: Dict[str, Any],
    ) -> Context:
        """
        Enrich context with a new question and its associated API data.

        Args:
            context: The context to enrich
            question: The user question
            intent: The classified intent
            endpoints_used: List of endpoints called
            api_data: The API response data

        Returns:
            Updated context
        """
        # Create user question entry
        user_question: UserQuestion = {
            "question": question,
            "intent": intent,
            "timestamp": datetime.now().isoformat(),
            "endpoints_used": endpoints_used,
        }

        # Add question to history
        context["user_questions"].append(user_question)

        # Merge new API data into collected data (avoid duplicates)
        for key, value in api_data.items():
            if key not in context["data_collected"]:
                context["data_collected"][key] = value

        # Update context metadata
        context["updated_at"] = datetime.now().isoformat()

        # Recalculate size
        context["context_size"] = sys.getsizeof(json.dumps(context))

        # Trim if size exceeded
        if context["context_size"] > context["max_context_size"]:
            context = self._trim_context(context)

        return context

    def _trim_context(self, context: Context) -> Context:
        """
        Trim context to fit within max size by removing oldest questions.

        Args:
            context: The context to trim

        Returns:
            Trimmed context
        """
        logger.info(f"Trimming context {context['context_id']} (size: {context['context_size']})")

        # Remove oldest questions until we fit
        while context["context_size"] > context["max_context_size"] and len(context["user_questions"]) > 1:
            context["user_questions"].pop(0)
            context["context_size"] = sys.getsizeof(json.dumps(context))

        logger.info(f"Context trimmed to size: {context['context_size']}")
        return context

    def save_context(self, context: Context) -> bool:
        """
        Save context to Redis.

        Args:
            context: The context to save

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available, context not saved")
            return False

        try:
            context_json = json.dumps(context)
            self.redis_client.setex(
                context["context_id"],
                self.CONTEXT_TTL,
                context_json
            )
            logger.info(f"Saved context {context['context_id']} to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to save context to Redis: {e}")
            return False

    def get_context(self, context_id: str) -> Optional[Context]:
        """
        Retrieve context from Redis.

        Args:
            context_id: The context ID

        Returns:
            Context dict if found, None otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available")
            return None

        try:
            context_json = self.redis_client.get(context_id)
            if context_json:
                context = json.loads(context_json)
                logger.info(f"Retrieved context {context_id} from Redis")
                return context
            else:
                logger.info(f"Context {context_id} not found in Redis")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve context from Redis: {e}")
            return None

    def delete_context(self, context_id: str) -> bool:
        """
        Delete context from Redis.

        Args:
            context_id: The context ID

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.redis_client:
            logger.warning("Redis client not available")
            return False

        try:
            deleted = self.redis_client.delete(context_id)
            if deleted:
                logger.info(f"Deleted context {context_id} from Redis")
                return True
            else:
                logger.info(f"Context {context_id} not found in Redis")
                return False
        except Exception as e:
            logger.error(f"Failed to delete context from Redis: {e}")
            return False

    def list_active_contexts(self) -> List[str]:
        """
        List all active context IDs in Redis.

        Returns:
            List of context IDs
        """
        if not self.redis_client:
            logger.warning("Redis client not available")
            return []

        try:
            # Get all keys matching our context patterns
            match_keys = self.redis_client.keys("match_*")
            league_keys = self.redis_client.keys("league_*")
            all_keys = match_keys + league_keys
            logger.info(f"Found {len(all_keys)} active contexts")
            return all_keys
        except Exception as e:
            logger.error(f"Failed to list contexts from Redis: {e}")
            return []
