"""
Entity resolution cache for reducing API calls.

This module caches entity resolutions (team names → IDs, league names → IDs, etc.)
to avoid repeated API calls for the same entities.

Examples:
- "PSG" → {team_id: 85, name: "Paris Saint Germain", league_id: 61}
- "Ligue 1" → {league_id: 61, name: "Ligue 1", country: "France"}
- "Mbappé" → {player_id: 276, name: "Kylian Mbappé", team_id: 541}
"""

import asyncio
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import timedelta
import redis.asyncio as redis


logger = logging.getLogger(__name__)


class EntityResolutionCache:
    """
    Cache for entity resolutions.

    Reduces API calls by caching mappings like:
    - Team name → team data
    - League name → league data
    - Player name → player data
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 7 * 24 * 3600,  # 7 days
    ):
        """
        Initialize entity resolution cache.

        Args:
            redis_client: Optional redis client (will create if None)
            redis_url: Redis connection URL
            default_ttl: Default TTL for cached entities (7 days)
        """
        self.redis = redis_client
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.prefix = "lucide:entity:"

    async def _ensure_connected(self):
        """Ensure Redis connection is established."""
        if self.redis is None:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)

    def _normalize_name(self, name: str) -> str:
        """
        Normalize entity name for caching.

        Handles:
        - Lowercase
        - Remove accents
        - Remove special characters
        - Trim whitespace

        Args:
            name: Entity name

        Returns:
            Normalized name

        Examples:
            >>> cache = EntityResolutionCache()
            >>> cache._normalize_name("Paris Saint-Germain")
            'paris saint germain'
            >>> cache._normalize_name("  PSG  ")
            'psg'
        """
        import unicodedata

        # Remove accents
        name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        )

        # Lowercase, remove special chars, trim
        name = name.lower()
        name = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name)
        name = ' '.join(name.split())  # Normalize whitespace

        return name

    def _make_cache_key(self, entity_type: str, name: str) -> str:
        """
        Create cache key for entity.

        Args:
            entity_type: Type of entity ('team', 'league', 'player')
            name: Entity name

        Returns:
            Cache key

        Examples:
            >>> cache = EntityResolutionCache()
            >>> cache._make_cache_key("team", "PSG")
            'lucide:entity:team:psg'
        """
        normalized = self._normalize_name(name)
        return f"{self.prefix}{entity_type}:{normalized}"

    async def get_team(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached team data.

        Args:
            name: Team name

        Returns:
            Team data dict or None if not cached

        Examples:
            >>> cache = EntityResolutionCache()
            >>> team = await cache.get_team("PSG")
            >>> team['team_id']
            85
        """
        await self._ensure_connected()

        key = self._make_cache_key("team", name)

        try:
            import json
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Entity cache HIT for team: {name}")
                return json.loads(data)
            logger.debug(f"Entity cache MISS for team: {name}")
            return None
        except Exception as e:
            logger.warning(f"Error getting team from cache: {e}")
            return None

    async def set_team(self, name: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache team data.

        Args:
            name: Team name
            data: Team data (must include team_id)
            ttl: Optional TTL (default: 7 days)

        Examples:
            >>> cache = EntityResolutionCache()
            >>> await cache.set_team("PSG", {
            ...     "team_id": 85,
            ...     "name": "Paris Saint Germain",
            ...     "league_id": 61,
            ...     "country": "France"
            ... })
        """
        await self._ensure_connected()

        if "team_id" not in data:
            logger.warning(f"Cannot cache team without team_id: {name}")
            return

        key = self._make_cache_key("team", name)
        ttl = ttl or self.default_ttl

        try:
            import json
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached team: {name} → team_id={data['team_id']}")
        except Exception as e:
            logger.warning(f"Error caching team: {e}")

    async def get_league(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached league data.

        Args:
            name: League name

        Returns:
            League data dict or None

        Examples:
            >>> cache = EntityResolutionCache()
            >>> league = await cache.get_league("Ligue 1")
            >>> league['league_id']
            61
        """
        await self._ensure_connected()

        key = self._make_cache_key("league", name)

        try:
            import json
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Entity cache HIT for league: {name}")
                return json.loads(data)
            logger.debug(f"Entity cache MISS for league: {name}")
            return None
        except Exception as e:
            logger.warning(f"Error getting league from cache: {e}")
            return None

    async def set_league(self, name: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache league data.

        Args:
            name: League name
            data: League data (must include league_id)
            ttl: Optional TTL

        Examples:
            >>> await cache.set_league("Ligue 1", {
            ...     "league_id": 61,
            ...     "name": "Ligue 1",
            ...     "country": "France",
            ...     "type": "League"
            ... })
        """
        await self._ensure_connected()

        if "league_id" not in data:
            logger.warning(f"Cannot cache league without league_id: {name}")
            return

        key = self._make_cache_key("league", name)
        ttl = ttl or self.default_ttl

        try:
            import json
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached league: {name} → league_id={data['league_id']}")
        except Exception as e:
            logger.warning(f"Error caching league: {e}")

    async def get_player(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached player data.

        Args:
            name: Player name

        Returns:
            Player data dict or None

        Examples:
            >>> cache = EntityResolutionCache()
            >>> player = await cache.get_player("Mbappé")
            >>> player['player_id']
            276
        """
        await self._ensure_connected()

        key = self._make_cache_key("player", name)

        try:
            import json
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Entity cache HIT for player: {name}")
                return json.loads(data)
            logger.debug(f"Entity cache MISS for player: {name}")
            return None
        except Exception as e:
            logger.warning(f"Error getting player from cache: {e}")
            return None

    async def set_player(self, name: str, data: Dict[str, Any], ttl: Optional[int] = None):
        """
        Cache player data.

        Args:
            name: Player name
            data: Player data (must include player_id)
            ttl: Optional TTL

        Examples:
            >>> await cache.set_player("Mbappé", {
            ...     "player_id": 276,
            ...     "name": "Kylian Mbappé",
            ...     "team_id": 541,
            ...     "position": "Attacker"
            ... })
        """
        await self._ensure_connected()

        if "player_id" not in data:
            logger.warning(f"Cannot cache player without player_id: {name}")
            return

        key = self._make_cache_key("player", name)
        ttl = ttl or self.default_ttl

        try:
            import json
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached player: {name} → player_id={data['player_id']}")
        except Exception as e:
            logger.warning(f"Error caching player: {e}")

    async def invalidate_team(self, name: str):
        """Invalidate cached team data."""
        await self._ensure_connected()
        key = self._make_cache_key("team", name)
        await self.redis.delete(key)
        logger.debug(f"Invalidated team cache: {name}")

    async def invalidate_league(self, name: str):
        """Invalidate cached league data."""
        await self._ensure_connected()
        key = self._make_cache_key("league", name)
        await self.redis.delete(key)
        logger.debug(f"Invalidated league cache: {name}")

    async def invalidate_player(self, name: str):
        """Invalidate cached player data."""
        await self._ensure_connected()
        key = self._make_cache_key("player", name)
        await self.redis.delete(key)
        logger.debug(f"Invalidated player cache: {name}")

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()


# Singleton instance
_entity_cache = None


async def get_entity_cache() -> EntityResolutionCache:
    """
    Get singleton entity cache instance.

    Returns:
        Shared EntityResolutionCache instance

    Examples:
        >>> cache = await get_entity_cache()
        >>> team = await cache.get_team("PSG")
    """
    global _entity_cache
    if _entity_cache is None:
        _entity_cache = EntityResolutionCache()
        await _entity_cache._ensure_connected()
    return _entity_cache
