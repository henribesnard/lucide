"""
Context Selection Keyboards

Inline keyboards for selecting leagues, matches, teams, players.
"""
from telegram import InlineKeyboardButton


def get_main_context_menu(current_context: dict = None):
    """
    Get the main context selection menu based on current context.

    Logic:
    - Par défaut (pas de contexte): seulement "League"
    - Avec League: "Match", "Team", "Clear"
    - Avec League + Match: "Team" (2 équipes), "Player", "Clear"
    - Avec League + Team: "Player", "Clear"
    - Avec League + Match + Team: "Player", "Clear"

    Args:
        current_context: Dictionary with 'league', 'match', 'team', 'player' keys

    Returns:
        List of keyboard rows
    """
    if current_context is None:
        current_context = {}

    keyboard = []

    # Par défaut: seulement League
    if not current_context.get("league"):
        keyboard.append([
            InlineKeyboardButton("🏆 Select League", callback_data="ctx_league"),
        ])
        return keyboard

    # Avec League choisie
    league_selected = current_context.get("league")
    match_selected = current_context.get("match")
    team_selected = current_context.get("team")
    player_selected = current_context.get("player")

    # Si League + Match + Team + Player: seulement Clear
    if league_selected and match_selected and team_selected and player_selected:
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Si League + Match + Player: Player et Clear (pas de Team car déjà player choisi)
    if league_selected and match_selected and player_selected:
        keyboard.append([
            InlineKeyboardButton("🎯 Change Player", callback_data="ctx_player"),
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Si League + Team + Player: seulement Clear
    if league_selected and team_selected and player_selected:
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Si League + Match: Team (2 équipes) et Player (joueurs des 2 équipes)
    if league_selected and match_selected:
        keyboard.append([
            InlineKeyboardButton("👥 Select Team", callback_data="ctx_team"),
            InlineKeyboardButton("🎯 Select Player", callback_data="ctx_player"),
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Si League + Team: Player
    if league_selected and team_selected:
        keyboard.append([
            InlineKeyboardButton("🎯 Select Player", callback_data="ctx_player"),
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Si seulement League: Match et Team
    if league_selected:
        keyboard.append([
            InlineKeyboardButton("⚽ Select Match", callback_data="ctx_match"),
            InlineKeyboardButton("👥 Select Team", callback_data="ctx_team"),
        ])
        keyboard.append([
            InlineKeyboardButton("❌ Clear Context", callback_data="ctx_clear"),
        ])
        return keyboard

    # Fallback: seulement League
    keyboard.append([
        InlineKeyboardButton("🏆 Select League", callback_data="ctx_league"),
    ])
    return keyboard


def get_league_selector(leagues: list):
    """
    Get keyboard for selecting a specific league.

    Args:
        leagues: List of league dictionaries with 'id', 'name', 'flag'

    Returns:
        List of keyboard rows
    """
    keyboard = []

    for league in leagues:
        flag = league.get("flag", "🏆")
        name = league.get("name", "Unknown")
        league_id = league.get("id")

        keyboard.append([
            InlineKeyboardButton(
                f"{flag} {name}",
                callback_data=f"league_{league_id}",
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="ctx_back"),
    ])

    return keyboard


def get_match_selector(matches: list):
    """
    Get keyboard for selecting a specific match.

    Args:
        matches: List of match dictionaries

    Returns:
        List of keyboard rows
    """
    keyboard = []

    for match in matches:
        home_team = match.get("teams", {}).get("home", {}).get("name", "?")
        away_team = match.get("teams", {}).get("away", {}).get("name", "?")
        match_id = match.get("fixture", {}).get("id")
        date = match.get("fixture", {}).get("date", "")[:10]  # YYYY-MM-DD

        keyboard.append([
            InlineKeyboardButton(
                f"{home_team} vs {away_team} ({date})",
                callback_data=f"match_{match_id}",
            )
        ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="ctx_back"),
    ])

    return keyboard
