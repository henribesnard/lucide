"""
Session manager using Redis for scalable, persistent sessions.

SECURITY & SCALABILITY:
- Sessions stored in Redis (not in-memory)
- Automatic expiration (TTL)
- Works with multiple server instances
- Survives server restarts
"""

import json
import logging
from typing import Optional
from datetime import timedelta

import redis.asyncio as redis
from backend.config import settings

logger = logging.getLogger(__name__)

# Session TTL: 1 hour of inactivity
SESSION_TTL = timedelta(hours=1)


class SessionManager:
    """Manages user sessions in Redis."""

    def __init__(self, redis_url: str = None):
        """
        Initialize session manager.

        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self):
        """Connect to Redis."""
        if self._initialized:
            return

        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Session manager initialized with Redis")
        except redis.ConnectionError as exc:
            logger.error(f"Failed to connect to Redis: {exc}")
            raise RuntimeError(f"Redis connection failed: {exc}") from exc

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False
            logger.info("Session manager closed")

    def _get_key(self, session_id: str) -> str:
        """Get Redis key for session."""
        return f"session:{session_id}"

    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Retrieve session data.

        Args:
            session_id: Unique session identifier

        Returns:
            Session data dict or None if not found
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(session_id)
            data = await self.redis_client.get(key)

            if data:
                # Refresh TTL on access
                await self.redis_client.expire(key, SESSION_TTL)
                return json.loads(data)

            return None
        except Exception as exc:
            logger.error(f"Error getting session {session_id}: {exc}")
            return None

    async def set_session(self, session_id: str, data: dict) -> bool:
        """
        Store session data.

        Args:
            session_id: Unique session identifier
            data: Session data to store

        Returns:
            True if successful, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(session_id)
            await self.redis_client.setex(
                key,
                SESSION_TTL,
                json.dumps(data)
            )
            logger.debug(f"Session {session_id} stored")
            return True
        except Exception as exc:
            logger.error(f"Error setting session {session_id}: {exc}")
            return False

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(session_id)
            result = await self.redis_client.delete(key)
            logger.debug(f"Session {session_id} deleted")
            return bool(result)
        except Exception as exc:
            logger.error(f"Error deleting session {session_id}: {exc}")
            return False

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists.

        Args:
            session_id: Session ID to check

        Returns:
            True if exists, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        try:
            key = self._get_key(session_id)
            return bool(await self.redis_client.exists(key))
        except Exception as exc:
            logger.error(f"Error checking session {session_id}: {exc}")
            return False


# Global session manager instance
session_manager = SessionManager()
