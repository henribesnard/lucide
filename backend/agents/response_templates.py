"""
Response templates for simple intents to avoid LLM calls.

This module provides template-based responses for straightforward queries
like standings, top scorers, etc. to reduce latency and LLM costs.
"""

from typing import Dict, Any, List, Optional
from backend.agents.types import IntentResult, AnalysisResult, ToolCallResult


def can_use_template(intent: IntentResult, context: Optional[Dict[str, Any]]) -> bool:
    """
    Determine if a template can be used for this intent.

    Args:
        intent: The detected intent
        context: Optional context

    Returns:
        True if a template can be used
    """
    template_intents = {
        "classement_ligue",
        "standings",
        "top_performers",
        "top_scorers",
        "top_assists",
        "top_cartons",
        "top_yellow_cards",
        "top_red_cards",
    }
    return intent.intent in template_intents


def generate_standings_response(
    tool_results: List[ToolCallResult],
    language: str = "fr",
) -> str:
    """Generate standings response from tool results."""
    standings_tool = next(
        (tr for tr in tool_results if tr.name == "standings"),
        None
    )

    if not standings_tool or not isinstance(standings_tool.output, dict):
        if language == "fr":
            return "❌ Impossible de récupérer le classement pour le moment."
        return "❌ Unable to retrieve standings at the moment."

    standings_data = standings_tool.output.get("standings", [])
    if not standings_data or not isinstance(standings_data, list):
        if language == "fr":
            return "❌ Aucune donnée de classement disponible."
        return "❌ No standings data available."

    # standings_data is already a list of teams (summarized format)
    # Each item is: {"position": 1, "team": "Liverpool", "points": 50, ...}
    main_standings = standings_data

    if not main_standings:
        if language == "fr":
            return "❌ Le classement est vide."
        return "❌ Standings are empty."

    # Build response
    if language == "fr":
        response = "📊 **Classement**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Équipe':<30} {'Pts':<5} {'J':<4} {'V-N-D':<10} {'Buts':<10}\n"
        response += "-" * 75 + "\n"

        for team in main_standings[:10]:  # Top 10
            # Summarized format: {"position": 1, "team": "Liverpool", "points": 50, ...}
            rank = team.get("position", "-")
            team_name = team.get("team", "Unknown")[:28]
            points = team.get("points", 0)
            played = team.get("played", 0)
            wins = team.get("wins", 0)
            draws = team.get("draws", 0)
            losses = team.get("losses", 0)
            goals_for = team.get("goals_for", 0)
            goals_against = team.get("goals_against", 0)

            response += f"{rank:<4} {team_name:<30} {points:<5} {played:<4} {wins}-{draws}-{losses:<6} {goals_for}:{goals_against}\n"

        response += "```\n"
    else:
        response = "📊 **Standings**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Team':<30} {'Pts':<5} {'P':<4} {'W-D-L':<10} {'Goals':<10}\n"
        response += "-" * 75 + "\n"

        for team in main_standings[:10]:
            # Summarized format: {"position": 1, "team": "Liverpool", "points": 50, ...}
            rank = team.get("position", "-")
            team_name = team.get("team", "Unknown")[:28]
            points = team.get("points", 0)
            played = team.get("played", 0)
            wins = team.get("wins", 0)
            draws = team.get("draws", 0)
            losses = team.get("losses", 0)
            goals_for = team.get("goals_for", 0)
            goals_against = team.get("goals_against", 0)

            response += f"{rank:<4} {team_name:<30} {points:<5} {played:<4} {wins}-{draws}-{losses:<6} {goals_for}:{goals_against}\n"

        response += "```\n"

    return response


def generate_top_scorers_response(
    tool_results: List[ToolCallResult],
    language: str = "fr",
) -> str:
    """Generate top scorers response from tool results."""
    scorers_tool = next(
        (tr for tr in tool_results if tr.name == "top_scorers"),
        None
    )

    if not scorers_tool or not isinstance(scorers_tool.output, dict):
        if language == "fr":
            return "❌ Impossible de récupérer les meilleurs buteurs."
        return "❌ Unable to retrieve top scorers."

    scorers = scorers_tool.output.get("top_scorers", [])
    if not scorers:
        if language == "fr":
            return "❌ Aucun buteur disponible."
        return "❌ No scorers available."

    # Build response
    if language == "fr":
        response = "⚽ **Meilleurs buteurs**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Joueur':<30} {'Équipe':<25} {'Buts':<6}\n"
        response += "-" * 70 + "\n"

        for idx, player_data in enumerate(scorers[:15], 1):
            # Data is already summarized by the tool
            name = player_data.get("name", "Unknown")[:28]
            team_name = player_data.get("team", "Unknown")[:23] if player_data.get("team") else "Unknown"
            goals = player_data.get("goals", 0) or 0

            response += f"{idx:<4} {name:<30} {team_name:<25} {goals:<6}\n"

        response += "```\n"
    else:
        response = "⚽ **Top Scorers**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Player':<30} {'Team':<25} {'Goals':<6}\n"
        response += "-" * 70 + "\n"

        for idx, player_data in enumerate(scorers[:15], 1):
            # Data is already summarized by the tool
            name = player_data.get("name", "Unknown")[:28]
            team_name = player_data.get("team", "Unknown")[:23] if player_data.get("team") else "Unknown"
            goals = player_data.get("goals", 0) or 0

            response += f"{idx:<4} {name:<30} {team_name:<25} {goals:<6}\n"

        response += "```\n"

    return response


def generate_top_assists_response(
    tool_results: List[ToolCallResult],
    language: str = "fr",
) -> str:
    """Generate top assists response from tool results."""
    assists_tool = next(
        (tr for tr in tool_results if tr.name == "top_assists"),
        None
    )

    if not assists_tool or not isinstance(assists_tool.output, dict):
        if language == "fr":
            return "❌ Impossible de récupérer les meilleurs passeurs."
        return "❌ Unable to retrieve top assists."

    assisters = assists_tool.output.get("top_assists", [])
    if not assisters:
        if language == "fr":
            return "❌ Aucun passeur disponible."
        return "❌ No assists available."

    # Build response
    if language == "fr":
        response = "🎯 **Meilleurs passeurs**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Joueur':<30} {'Équipe':<25} {'Passes':<6}\n"
        response += "-" * 70 + "\n"

        for idx, player_data in enumerate(assisters[:15], 1):
            # Data is already summarized by the tool
            name = player_data.get("name", "Unknown")[:28]
            team_name = player_data.get("team", "Unknown")[:23] if player_data.get("team") else "Unknown"
            assists = player_data.get("assists", 0) or 0

            response += f"{idx:<4} {name:<30} {team_name:<25} {assists:<6}\n"

        response += "```\n"
    else:
        response = "🎯 **Top Assists**\n\n"
        response += "```\n"
        response += f"{'#':<4} {'Player':<30} {'Team':<25} {'Assists':<6}\n"
        response += "-" * 70 + "\n"

        for idx, player_data in enumerate(assisters[:15], 1):
            # Data is already summarized by the tool
            name = player_data.get("name", "Unknown")[:28]
            team_name = player_data.get("team", "Unknown")[:23] if player_data.get("team") else "Unknown"
            assists = player_data.get("assists", 0) or 0

            response += f"{idx:<4} {name:<30} {team_name:<25} {assists:<6}\n"

        response += "```\n"

    return response


def generate_template_response(
    intent: IntentResult,
    tool_results: List[ToolCallResult],
    analysis: AnalysisResult,
    language: str = "fr",
) -> Optional[str]:
    """
    Generate a template-based response if applicable.

    Args:
        intent: The detected intent
        tool_results: Results from tool execution
        analysis: Analysis result (may be minimal for template intents)
        language: Language code ('fr' or 'en')

    Returns:
        Template-based response or None if no template applies
    """
    if not tool_results:
        return None

    # Route to appropriate template
    if intent.intent in ("classement_ligue", "standings"):
        return generate_standings_response(tool_results, language)

    if intent.intent in ("top_performers", "top_scorers"):
        return generate_top_scorers_response(tool_results, language)

    if intent.intent == "top_assists":
        return generate_top_assists_response(tool_results, language)

    # Add more templates as needed
    return None
