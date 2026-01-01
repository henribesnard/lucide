"""
Season inference logic for football data.

This module handles automatic season detection from various inputs:
- Explicit years in user message
- Relative season phrases ("last season", "saison dernière")
- Context-based inference (match dates)
- Default to current season
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any


# Patterns
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

RELATIVE_SEASON_PHRASES = (
    "last season",
    "previous season",
    "last year",
    "previous year",
    "past season",
    "saison derniere",
    "derniere saison",
    "saison precedente",
    "saison passee",
    "annee derniere",
    "l an dernier",
    "lan dernier",
)

# Tools that require season parameter
SEASONAL_TOOLS = {
    "standings",
    "top_scorers",
    "top_assists",
    "top_yellow_cards",
    "top_red_cards",
    "team_statistics",
    "fixture_rounds",
    "player_statistics",
    "injuries",
}


def current_season_year(reference: Optional[datetime] = None) -> int:
    """
    Get current football season year.

    Football seasons typically start in August/September, so:
    - January-July: season is previous year
    - August-December: season is current year

    Args:
        reference: Reference datetime (default: now)

    Returns:
        Season year (e.g., 2024 for 2024-2025 season)

    Examples:
        >>> current_season_year(datetime(2024, 3, 15))
        2023  # March 2024 is in 2023-2024 season
        >>> current_season_year(datetime(2024, 9, 15))
        2024  # September 2024 is in 2024-2025 season
    """
    now = reference or datetime.utcnow()
    return now.year if now.month >= 8 else now.year - 1


def season_from_date(date_str: Optional[str]) -> Optional[int]:
    """
    Extract season year from date string.

    Args:
        date_str: ISO date string (e.g., "2024-03-15T20:00:00Z")

    Returns:
        Season year or None if parsing fails

    Examples:
        >>> season_from_date("2024-03-15T20:00:00Z")
        2023  # March is before August
        >>> season_from_date("2024-09-15T20:00:00Z")
        2024  # September is after August
    """
    if not date_str:
        return None
    try:
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return parsed.year if parsed.month >= 8 else parsed.year - 1
    except Exception:
        return None


def message_mentions_explicit_year(message: str) -> bool:
    """
    Check if message contains explicit year mention.

    Args:
        message: User message

    Returns:
        True if year is mentioned (e.g., "2023", "2024")

    Examples:
        >>> message_mentions_explicit_year("Stats PSG 2023")
        True
        >>> message_mentions_explicit_year("Stats PSG saison dernière")
        False
    """
    return bool(YEAR_PATTERN.search(message))


def message_mentions_relative_season(message: str) -> bool:
    """
    Check if message contains relative season phrase.

    Args:
        message: User message

    Returns:
        True if relative season phrase detected

    Examples:
        >>> message_mentions_relative_season("Stats last season")
        True
        >>> message_mentions_relative_season("Stats saison dernière")
        True
        >>> message_mentions_relative_season("Stats actuelles")
        False
    """
    lowered = message.lower()
    return any(phrase in lowered for phrase in RELATIVE_SEASON_PHRASES)


def default_season_for_request(
    message: str,
    context: Optional[Dict[str, Any]]
) -> Optional[int]:
    """
    Determine default season for a request.

    Priority:
    1. Explicit year/relative phrase in message → None (LLM will handle)
    2. Match date in context → season from date
    3. Season in context → use context season
    4. Default → current season

    Args:
        message: User message
        context: Request context

    Returns:
        Season year or None if should be handled by LLM

    Examples:
        >>> default_season_for_request("Stats PSG 2023", {})
        None  # Explicit year, let LLM handle

        >>> default_season_for_request("Stats PSG", {"match_date": "2023-03-15"})
        2022  # Inferred from match date

        >>> default_season_for_request("Stats PSG", {})
        2024  # Current season (assuming 2024-2025)
    """
    # If explicit year or relative phrase, let LLM handle
    if message_mentions_explicit_year(message) or message_mentions_relative_season(message):
        return None

    # Try to infer from context
    if context:
        # From match date
        match_date = context.get("match_date")
        inferred = season_from_date(match_date)
        if inferred:
            return inferred

        # From context season
        context_season = context.get("season")
        if isinstance(context_season, int):
            return context_season

    # Default to current season
    return current_season_year()


def apply_season_to_arguments(
    tool_name: str,
    arguments: Dict[str, Any],
    default_season: Optional[int]
) -> Dict[str, Any]:
    """
    Apply default season to tool arguments if needed.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        default_season: Default season to apply

    Returns:
        Updated arguments with season

    Examples:
        >>> apply_season_to_arguments("standings", {}, 2024)
        {'season': 2024}

        >>> apply_season_to_arguments("standings", {'season': 2023}, 2024)
        {'season': 2023}  # Keep explicit season

        >>> apply_season_to_arguments("fixtures_search", {}, 2024)
        {}  # Not a seasonal tool
    """
    if tool_name not in SEASONAL_TOOLS:
        return arguments

    if default_season and "season" not in arguments:
        arguments["season"] = default_season

    return arguments


def is_seasonal_tool(tool_name: str) -> bool:
    """
    Check if a tool requires season parameter.

    Args:
        tool_name: Name of the tool

    Returns:
        True if tool is seasonal

    Examples:
        >>> is_seasonal_tool("standings")
        True
        >>> is_seasonal_tool("fixtures_search")
        False
    """
    return tool_name in SEASONAL_TOOLS
