"""
Intelligent cache module for autonomous agents.

This module contains the intelligent cache manager that handles multi-user caching
with TTL adaptation, key normalization, and cache invalidation strategies.
"""

from .intelligent_cache_manager import IntelligentCacheManager, CacheKeyGenerator

__all__ = ['IntelligentCacheManager', 'CacheKeyGenerator']
