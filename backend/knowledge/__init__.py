"""
Knowledge base module for autonomous agents.

This module contains the endpoint knowledge base that stores metadata
about all API-Football endpoints, their use cases, parameters, and caching strategies.
"""

from .endpoint_knowledge_base import EndpointKnowledgeBase, EndpointMetadata

__all__ = ['EndpointKnowledgeBase', 'EndpointMetadata']
