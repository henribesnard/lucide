"""
Forced tools strategy for ensuring critical data collection.

This module defines which tools are mandatory for specific intents,
ensuring comprehensive data collection for match analysis and other
critical queries.
"""

import logging
from typing import Dict, Set, List, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ToolRequirement:
    """Defines a required tool and its configuration."""
    name: str
    required: bool = True
    fallback_allowed: bool = False
    description: str = ""


class ForcedToolsStrategy:
    """
    Strategy for forcing critical tools per intent.

    Ensures that match analysis, stats queries, and other critical
    intents collect all necessary data even if LLM misses some tools.
    """

    def __init__(self):
        self.strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> Dict[str, List[ToolRequirement]]:
        """
        Initialize tool requirements per intent.

        Returns:
            Dict mapping intent names to required tools
        """
        return {
            # Match analysis intents - most comprehensive
            "analyse_rencontre": [
                ToolRequirement("fixtures_search", description="Match details and status"),
                ToolRequirement("team_last_fixtures", description="Recent form for both teams"),
                ToolRequirement("standings", description="League table position"),
                ToolRequirement("head_to_head", description="Historical matchups"),
                ToolRequirement("team_statistics", description="Season stats for both teams", fallback_allowed=True),
                ToolRequirement("fixture_lineups", description="Team lineups", fallback_allowed=True),
                ToolRequirement("injuries", description="Injury reports"),
                ToolRequirement("fixture_rounds", description="Current matchday"),
                ToolRequirement("league_type", description="Competition type (Cup/League)"),
                ToolRequirement("team_form_stats", description="Recent form statistics"),
                ToolRequirement("top_scorers", description="League top scorers"),
                ToolRequirement("top_assists", description="League top assisters"),
            ],

            "match_analysis": [
                # Same as analyse_rencontre
                ToolRequirement("fixtures_search", description="Match details"),
                ToolRequirement("team_last_fixtures", description="Recent form"),
                ToolRequirement("standings", description="League position"),
                ToolRequirement("head_to_head", description="H2H history"),
                ToolRequirement("team_statistics", description="Season stats", fallback_allowed=True),
                ToolRequirement("fixture_lineups", description="Lineups", fallback_allowed=True),
                ToolRequirement("injuries", description="Injuries"),
                ToolRequirement("fixture_rounds", description="Matchday"),
                ToolRequirement("league_type", description="Competition type"),
                ToolRequirement("team_form_stats", description="Form stats"),
                ToolRequirement("top_scorers", description="Top scorers"),
                ToolRequirement("top_assists", description="Top assists"),
            ],

            # Match stats intents
            "stats_final": [
                ToolRequirement("fixtures_search", description="Match result"),
                ToolRequirement("fixture_statistics", description="Match statistics"),
                ToolRequirement("fixture_events", description="Match events"),
            ],

            "stats_live": [
                ToolRequirement("fixtures_search", description="Live match info"),
                ToolRequirement("fixture_statistics", description="Live statistics"),
            ],

            # Result-oriented intents
            "result_final": [
                ToolRequirement("fixtures_search", description="Final score"),
            ],

            "events_summary": [
                ToolRequirement("fixtures_search", description="Match info"),
                ToolRequirement("fixture_events", description="Match events"),
            ],

            "players_performance": [
                ToolRequirement("fixtures_search", description="Match info"),
                ToolRequirement("fixture_players", description="Player statistics"),
            ],

            # Player context intents
            "stats_joueur": [
                # Handled separately in _force_player_stats_tools
            ],
        }

    def get_required_tools(self, intent: str) -> List[ToolRequirement]:
        """
        Get required tools for an intent.

        Args:
            intent: Intent name

        Returns:
            List of required tools

        Examples:
            >>> strategy = ForcedToolsStrategy()
            >>> tools = strategy.get_required_tools("analyse_rencontre")
            >>> len(tools)
            12
        """
        return self.strategies.get(intent, [])

    def get_missing_tools(
        self,
        intent: str,
        available_tools: Set[str]
    ) -> List[ToolRequirement]:
        """
        Identify which required tools are missing.

        Args:
            intent: Intent name
            available_tools: Set of already-called tool names

        Returns:
            List of missing required tools

        Examples:
            >>> strategy = ForcedToolsStrategy()
            >>> available = {"fixtures_search", "standings"}
            >>> missing = strategy.get_missing_tools("analyse_rencontre", available)
            >>> "team_last_fixtures" in [t.name for t in missing]
            True
        """
        required = self.get_required_tools(intent)
        missing = []

        for tool_req in required:
            if tool_req.required and tool_req.name not in available_tools:
                missing.append(tool_req)

        return missing

    def should_force_tools(self, intent: str) -> bool:
        """
        Check if this intent requires forcing tools.

        Args:
            intent: Intent name

        Returns:
            True if tools should be forced

        Examples:
            >>> strategy = ForcedToolsStrategy()
            >>> strategy.should_force_tools("analyse_rencontre")
            True
            >>> strategy.should_force_tools("info_generale")
            False
        """
        return intent in self.strategies

    def get_tool_execution_order(
        self,
        missing_tools: List[ToolRequirement]
    ) -> List[List[str]]:
        """
        Get execution order for missing tools (grouped by dependencies).

        Returns tools grouped by execution level:
        - Level 0: No dependencies (can run in parallel)
        - Level 1: Depends on Level 0 results
        - etc.

        Args:
            missing_tools: List of missing tools

        Returns:
            List of lists, each sublist can be executed in parallel

        Examples:
            >>> strategy = ForcedToolsStrategy()
            >>> missing = [
            ...     ToolRequirement("fixtures_search"),
            ...     ToolRequirement("team_last_fixtures"),
            ...     ToolRequirement("fixture_lineups")
            ... ]
            >>> order = strategy.get_tool_execution_order(missing)
            >>> len(order)
            2  # Level 0: fixtures_search, Level 1: team_last_fixtures, fixture_lineups
        """
        # Level 0: Core data (must run first)
        level_0 = ["fixtures_search", "standings"]

        # Level 1: Team/fixture data (depends on fixture_id from level 0)
        level_1 = [
            "team_last_fixtures",
            "team_statistics",
            "head_to_head",
            "team_form_stats",
            "fixture_lineups",
            "fixture_events",
            "fixture_statistics",
            "fixture_players",
            "injuries",
        ]

        # Level 2: League metadata (can run anytime)
        level_2 = [
            "fixture_rounds",
            "league_type",
            "top_scorers",
            "top_assists",
        ]

        missing_names = {tool.name for tool in missing_tools}

        execution_order = []

        # Add levels that have missing tools
        if any(name in missing_names for name in level_0):
            execution_order.append([name for name in level_0 if name in missing_names])

        if any(name in missing_names for name in level_1):
            execution_order.append([name for name in level_1 if name in missing_names])

        if any(name in missing_names for name in level_2):
            execution_order.append([name for name in level_2 if name in missing_names])

        return execution_order


# Singleton instance
_forced_tools_strategy = None


def get_forced_tools_strategy() -> ForcedToolsStrategy:
    """
    Get singleton instance of ForcedToolsStrategy.

    Returns:
        Shared ForcedToolsStrategy instance

    Examples:
        >>> strategy = get_forced_tools_strategy()
        >>> tools = strategy.get_required_tools("analyse_rencontre")
    """
    global _forced_tools_strategy
    if _forced_tools_strategy is None:
        _forced_tools_strategy = ForcedToolsStrategy()
    return _forced_tools_strategy
