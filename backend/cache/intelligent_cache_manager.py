"""
Intelligent Cache Manager for multi-user caching.

This module provides intelligent caching with TTL adaptation,
key normalization, and cache invalidation strategies.

Implemented in Phase 2.
"""

import hashlib
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from backend.monitoring.autonomous_agents_metrics import Metrics, logger


class CacheKeyGenerator:
    """
    Generates normalized cache keys for API calls.

    Features:
    - Team name normalization (PSG = Paris Saint-Germain)
    - Date normalization (various formats → YYYY-MM-DD)
    - Player name normalization
    - Sorted parameters for consistency
    - Multi-user cache sharing support
    """

    def __init__(self, cache_prefix: str = "lucide:cache:"):
        self.cache_prefix = cache_prefix

        # Team name aliases for normalization
        self.team_aliases = {
            # French teams
            "psg": "paris_saint_germain",
            "paris sg": "paris_saint_germain",
            "paris saint-germain": "paris_saint_germain",
            "paris saint germain": "paris_saint_germain",
            "om": "olympique_marseille",
            "marseille": "olympique_marseille",
            "olympique marseille": "olympique_marseille",
            "ol": "olympique_lyonnais",
            "lyon": "olympique_lyonnais",
            "olympique lyonnais": "olympique_lyonnais",
            "asse": "saint_etienne",
            "saint-etienne": "saint_etienne",
            "saint etienne": "saint_etienne",
            "as saint-etienne": "saint_etienne",

            # English teams
            "man utd": "manchester_united",
            "man united": "manchester_united",
            "manchester utd": "manchester_united",
            "manchester united": "manchester_united",
            "man city": "manchester_city",
            "manchester city": "manchester_city",
            "liverpool fc": "liverpool",
            "chelsea fc": "chelsea",
            "arsenal fc": "arsenal",
            "tottenham": "tottenham_hotspur",
            "spurs": "tottenham_hotspur",
            "tottenham hotspur": "tottenham_hotspur",

            # Spanish teams
            "real": "real_madrid",
            "real madrid cf": "real_madrid",
            "real madrid": "real_madrid",
            "barca": "barcelona",
            "fc barcelona": "barcelona",
            "barcelona": "barcelona",
            "atleti": "atletico_madrid",
            "atletico": "atletico_madrid",
            "atletico madrid": "atletico_madrid",

            # German teams
            "bayern": "bayern_munich",
            "fc bayern": "bayern_munich",
            "bayern munich": "bayern_munich",
            "bayern munchen": "bayern_munich",
            "bvb": "borussia_dortmund",
            "dortmund": "borussia_dortmund",
            "borussia dortmund": "borussia_dortmund",

            # Italian teams
            "juve": "juventus",
            "juventus fc": "juventus",
            "inter": "inter_milan",
            "inter milan": "inter_milan",
            "fc internazionale": "inter_milan",
            "ac milan": "milan",
            "milan": "milan",
        }

    def generate_key(self, endpoint_name: str, params: Dict[str, Any]) -> str:
        """
        Generate a normalized cache key.

        Args:
            endpoint_name: Name of the API endpoint
            params: Parameters for the API call

        Returns:
            Normalized cache key string

        Examples:
            >>> gen = CacheKeyGenerator()
            >>> gen.generate_key("fixtures", {"team": "PSG", "date": "2025-12-12"})
            'lucide:cache:fixtures:date:2025-12-12:team:paris_saint_germain'
        """
        normalized_params = self._normalize_params(endpoint_name, params)

        # Sort parameters for consistency
        sorted_params = sorted(normalized_params.items())

        # Create readable key parts
        key_parts = [endpoint_name]
        for key, value in sorted_params:
            # Convert value to string and make it URL-safe
            value_str = str(value).lower().replace(" ", "_")
            key_parts.append(f"{key}:{value_str}")

        # Add prefix at the end to avoid double colon
        return self.cache_prefix + ":".join(key_parts)

    def _normalize_params(self, endpoint_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parameters for consistent cache keys.

        Args:
            endpoint_name: Name of the endpoint
            params: Parameters to normalize

        Returns:
            Normalized parameters dictionary
        """
        normalized = {}

        for key, value in params.items():
            if value is None:
                continue

            # Normalize team names
            if key in ["team", "team_home", "team_away", "h2h"]:
                normalized[key] = self._normalize_team_name(value)

            # Normalize dates
            elif key in ["date", "from", "to", "date_from", "date_to"]:
                normalized[key] = self._normalize_date(value)

            # Normalize player names
            elif key in ["player", "player_name"]:
                normalized[key] = self._normalize_player_name(value)

            # Normalize h2h (ensure consistent order)
            elif key == "h2h" and "-" in str(value):
                normalized[key] = self._normalize_h2h(value)

            # Keep other params as-is but convert to string
            else:
                normalized[key] = value

        return normalized

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name to canonical form.

        Args:
            team_name: Team name in any form

        Returns:
            Normalized team name

        Examples:
            >>> gen = CacheKeyGenerator()
            >>> gen._normalize_team_name("PSG")
            'paris_saint_germain'
            >>> gen._normalize_team_name("Man Utd")
            'manchester_united'
        """
        if not isinstance(team_name, str):
            return str(team_name)

        # Convert to lowercase and strip
        team_lower = team_name.lower().strip()

        # Remove common prefixes/suffixes
        team_lower = re.sub(r'\b(fc|cf|ac|as|sc)\b', '', team_lower).strip()

        # Check aliases
        if team_lower in self.team_aliases:
            return self.team_aliases[team_lower]

        # Default: replace spaces with underscores
        return team_lower.replace(" ", "_").replace("-", "_")

    def _normalize_date(self, date_value: Any) -> str:
        """
        Normalize date to YYYY-MM-DD format.

        Args:
            date_value: Date in various formats

        Returns:
            Normalized date string (YYYY-MM-DD)

        Examples:
            >>> gen = CacheKeyGenerator()
            >>> gen._normalize_date("2025-12-12")
            '2025-12-12'
            >>> gen._normalize_date(datetime(2025, 12, 12))
            '2025-12-12'
        """
        if isinstance(date_value, datetime):
            return date_value.strftime("%Y-%m-%d")
        elif isinstance(date_value, date):
            return date_value.strftime("%Y-%m-%d")
        elif isinstance(date_value, str):
            # Try to parse various date formats
            date_str = date_value.strip()

            # Already in YYYY-MM-DD format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return date_str

            # Try common formats
            formats = [
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%m-%d-%Y",
                "%m/%d/%Y",
            ]

            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue

            # If all else fails, return as-is
            return date_str

        return str(date_value)

    def _normalize_player_name(self, player_name: str) -> str:
        """
        Normalize player name.

        Args:
            player_name: Player name

        Returns:
            Normalized player name

        Examples:
            >>> gen = CacheKeyGenerator()
            >>> gen._normalize_player_name("Kylian Mbappé")
            'kylian_mbappe'
        """
        if not isinstance(player_name, str):
            return str(player_name)

        # Convert to lowercase
        name = player_name.lower().strip()

        # Remove accents (basic approach)
        accents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ô': 'o', 'ö': 'o',
            'î': 'i', 'ï': 'i',
            'ç': 'c',
        }
        for accented, plain in accents.items():
            name = name.replace(accented, plain)

        # Replace spaces with underscores
        return name.replace(" ", "_").replace("-", "_")

    def _normalize_h2h(self, h2h_value: str) -> str:
        """
        Normalize head-to-head parameter (ensure consistent team order).

        Args:
            h2h_value: H2H string like "123-456"

        Returns:
            Normalized H2H with teams in sorted order

        Examples:
            >>> gen = CacheKeyGenerator()
            >>> gen._normalize_h2h("456-123")
            '123-456'
        """
        if not isinstance(h2h_value, str) or "-" not in h2h_value:
            return str(h2h_value)

        teams = h2h_value.split("-")
        if len(teams) != 2:
            return h2h_value

        # Sort team IDs to ensure consistent order
        team1, team2 = teams
        sorted_teams = sorted([team1.strip(), team2.strip()])

        return f"{sorted_teams[0]}-{sorted_teams[1]}"


class IntelligentCacheManager:
    """
    Intelligent cache manager with multi-user support.

    Features:
    - Redis-based async caching
    - TTL adaptation from EndpointKnowledgeBase
    - Cache invalidation by pattern
    - Multi-user cache sharing via normalized keys
    - Comprehensive metrics tracking
    """

    def __init__(self, redis_client, knowledge_base=None):
        """
        Initialize cache manager.

        Args:
            redis_client: Async Redis client
            knowledge_base: EndpointKnowledgeBase instance for TTL calculation
        """
        self.redis = redis_client
        self.knowledge_base = knowledge_base
        self.key_generator = CacheKeyGenerator()

    async def get(self, endpoint_name: str, params: Dict[str, Any],
                  match_status: Optional[str] = None) -> Optional[Any]:
        """
        Get cached data if available.

        Args:
            endpoint_name: Name of the API endpoint
            params: Parameters for the API call
            match_status: Optional match status for context

        Returns:
            Cached data if available, None otherwise
        """
        try:
            # Generate normalized key
            cache_key = self.key_generator.generate_key(endpoint_name, params)

            # Try to get from Redis
            cached_value = await self.redis.get(cache_key)

            if cached_value:
                # Cache hit
                Metrics.cache_hits.labels(endpoint_name=endpoint_name).inc()
                self._update_hit_rate(endpoint_name, is_hit=True)

                logger.info(
                    "cache_hit",
                    endpoint=endpoint_name,
                    cache_key=cache_key,
                    params=params
                )

                # Deserialize JSON
                return json.loads(cached_value)
            else:
                # Cache miss
                Metrics.cache_misses.labels(endpoint_name=endpoint_name).inc()
                self._update_hit_rate(endpoint_name, is_hit=False)

                logger.info(
                    "cache_miss",
                    endpoint=endpoint_name,
                    cache_key=cache_key,
                    params=params
                )

                return None

        except Exception as e:
            logger.error(
                "cache_get_error",
                endpoint=endpoint_name,
                error=str(e),
                params=params
            )
            return None

    async def set(self, endpoint_name: str, params: Dict[str, Any],
                  data: Any, match_status: Optional[str] = None):
        """
        Cache data with appropriate TTL.

        Args:
            endpoint_name: Name of the API endpoint
            params: Parameters for the API call
            data: Data to cache
            match_status: Optional match status for TTL calculation
        """
        try:
            # Generate normalized key
            cache_key = self.key_generator.generate_key(endpoint_name, params)

            # Calculate TTL
            ttl = self._calculate_ttl(endpoint_name, match_status)

            # Serialize data
            serialized_data = json.dumps(data)

            # Store in Redis
            if ttl == -1:
                # Indefinite cache (no expiration)
                await self.redis.set(cache_key, serialized_data)
            elif ttl > 0:
                # Cache with TTL
                await self.redis.setex(cache_key, ttl, serialized_data)
            else:
                # ttl == 0: Don't cache
                return

            # Track metrics
            Metrics.cache_sets.labels(endpoint_name=endpoint_name).inc()

            # Track TTL in histogram
            if self.knowledge_base:
                endpoint = self.knowledge_base.get_endpoint(endpoint_name)
                if endpoint:
                    Metrics.cache_ttl_seconds.labels(
                        cache_strategy=endpoint.cache_strategy.value
                    ).observe(ttl if ttl > 0 else 86400 * 365)  # 1 year for indefinite

            logger.info(
                "cache_set",
                endpoint=endpoint_name,
                cache_key=cache_key,
                ttl=ttl,
                params=params,
                data_size=len(serialized_data)
            )

        except Exception as e:
            logger.error(
                "cache_set_error",
                endpoint=endpoint_name,
                error=str(e),
                params=params
            )

    async def invalidate(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "lucide:cache:fixtures:*")

        Returns:
            Number of keys deleted
        """
        try:
            # Find matching keys
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)

            # Delete keys
            if keys:
                deleted = await self.redis.delete(*keys)

                logger.info(
                    "cache_invalidated",
                    pattern=pattern,
                    keys_deleted=deleted
                )

                return deleted

            return 0

        except Exception as e:
            logger.error(
                "cache_invalidate_error",
                pattern=pattern,
                error=str(e)
            )
            return 0

    async def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful
        """
        try:
            await self.redis.flushdb()
            logger.info("cache_cleared_all")
            return True
        except Exception as e:
            logger.error("cache_clear_all_error", error=str(e))
            return False

    def _calculate_ttl(self, endpoint_name: str, match_status: Optional[str] = None) -> int:
        """
        Calculate TTL using EndpointKnowledgeBase if available.

        Args:
            endpoint_name: Name of the endpoint
            match_status: Optional match status

        Returns:
            TTL in seconds (-1 for indefinite, 0 for no cache)
        """
        if self.knowledge_base:
            return self.knowledge_base.calculate_cache_ttl(endpoint_name, match_status)

        # Default fallback TTL
        return 300  # 5 minutes

    def _update_hit_rate(self, endpoint_name: str, is_hit: bool):
        """
        Update cache hit rate metric.

        Args:
            endpoint_name: Name of the endpoint
            is_hit: Whether it was a cache hit
        """
        try:
            # Get current counts
            hits = Metrics.cache_hits.labels(endpoint_name=endpoint_name)._value.get()
            misses = Metrics.cache_misses.labels(endpoint_name=endpoint_name)._value.get()
            total = hits + misses

            if total > 0:
                hit_rate = hits / total
                Metrics.cache_hit_rate.labels(endpoint_name=endpoint_name).set(hit_rate)
        except Exception:
            # Silently fail on metric update errors
            pass
