"""
Settings Keyboards

Inline keyboards for user settings and preferences.
"""
from telegram import InlineKeyboardButton


def get_settings_menu():
    """
    Get the main settings menu.

    Returns:
        List of keyboard rows
    """
    return [
        [
            InlineKeyboardButton("🌐 Language", callback_data="cmd_language"),
            InlineKeyboardButton("⭐ Subscription", callback_data="cmd_subscription"),
        ],
        [
            InlineKeyboardButton("🎯 Default Context", callback_data="settings_context"),
            InlineKeyboardButton("🤖 AI Model", callback_data="settings_model"),
        ],
        [
            InlineKeyboardButton("📦 Export Data", callback_data="cmd_export"),
            InlineKeyboardButton("🗑️ Delete Account", callback_data="settings_delete"),
        ],
    ]


def get_model_selector(current_model: str = "slow"):
    """
    Get keyboard for selecting AI model.

    Args:
        current_model: Current model selection ('slow', 'medium', 'fast')

    Returns:
        List of keyboard rows
    """
    models = [
        {"key": "slow", "name": "DeepSeek (Slow, Cheap)", "emoji": "🐢"},
        {"key": "medium", "name": "GPT-4o-mini (Balanced)", "emoji": "⚡"},
        {"key": "fast", "name": "GPT-4o (Fast, Premium)", "emoji": "🚀"},
    ]

    keyboard = []

    for model in models:
        is_current = "✅ " if model["key"] == current_model else ""
        keyboard.append([
            InlineKeyboardButton(
                f"{is_current}{model['emoji']} {model['name']}",
                callback_data=f"model_{model['key']}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Back", callback_data="cmd_settings"),
    ])

    return keyboard
