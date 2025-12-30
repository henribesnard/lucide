"""
Telegram Bot Callback Handlers

Handles callback queries from inline keyboards.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback query handler that routes to specific handlers based on callback_data.

    Callback data format: "action_subaction_params"
    Examples:
    - "ctx_league" - Open league selector
    - "lang_fr" - Switch to French
    - "conv_open_123" - Open conversation 123
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    callback_data = query.data
    logger.info(f"Callback query: {callback_data}")

    # Route to appropriate handler based on prefix
    if callback_data.startswith("ctx_"):
        await _handle_context_callback(update, context)
    elif callback_data.startswith("lang_"):
        await _handle_language_callback(update, context)
    elif callback_data.startswith("conv_"):
        await _handle_conversation_callback(update, context)
    elif callback_data.startswith("sub_"):
        await _handle_subscription_callback(update, context)
    elif callback_data.startswith("cmd_"):
        await _handle_command_callback(update, context)
    else:
        logger.warning(f"Unknown callback data: {callback_data}")
        await query.edit_message_text("❌ Unknown action. Please try again.")


async def _handle_context_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle context-related callbacks."""
    query = update.callback_query
    callback_data = query.data

    if callback_data == "ctx_league":
        # Show league selector
        await query.edit_message_text(
            "🏆 **Select a League**\n\nFetching popular leagues...",
            parse_mode=ParseMode.MARKDOWN,
        )
        # TODO: Implement league selector
    elif callback_data == "ctx_match":
        await query.edit_message_text(
            "⚽ **Select a Match**\n\nFetching upcoming matches...",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif callback_data == "ctx_team":
        await query.edit_message_text(
            "👥 **Select a Team**\n\nPlease search for a team...",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif callback_data == "ctx_clear":
        context.user_data["context"] = None
        await query.edit_message_text(
            "✅ **Context Cleared**\n\nAll context has been removed.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def _handle_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language switch callbacks."""
    from backend.telegram.services.user_service import UserService
    from backend.db.database import SessionLocal

    query = update.callback_query
    callback_data = query.data
    lang_code = callback_data.split("_")[1]  # "lang_fr" -> "fr"

    user_service = UserService(SessionLocal)
    try:
        user = update.effective_user
        user_record = await user_service.get_or_create_user(user)

        # Update language
        await user_service.update_language(user_record.user_id, lang_code)

        lang_name = "Français 🇫🇷" if lang_code == "fr" else "English 🇬🇧"

        await query.edit_message_text(
            f"✅ **Language Updated**\n\nYour language is now: {lang_name}",
            parse_mode=ParseMode.MARKDOWN,
        )

    except Exception as e:
        logger.error(f"Error updating language: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ Failed to update language. Please try again.",
            parse_mode=ParseMode.MARKDOWN,
        )
    finally:
        await user_service.close()


async def _handle_conversation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversation-related callbacks."""
    query = update.callback_query
    callback_data = query.data

    if callback_data.startswith("conv_open_"):
        conversation_id = callback_data.replace("conv_open_", "")
        context.user_data["active_conversation_id"] = conversation_id

        await query.edit_message_text(
            f"✅ **Conversation Loaded**\n\nContinue your conversation...",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif callback_data == "conv_delete_mode":
        await query.edit_message_text(
            "🗑️ **Delete Mode**\n\nSelect conversations to delete.\n(Feature coming soon)",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif callback_data == "conv_load_more":
        await query.edit_message_text(
            "🔄 **Loading More**\n\n(Feature coming soon)",
            parse_mode=ParseMode.MARKDOWN,
        )


async def _handle_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription-related callbacks."""
    query = update.callback_query
    callback_data = query.data

    if callback_data == "sub_premium":
        await query.edit_message_text(
            "⭐ **Upgrade to Premium**\n\n"
            "Premium features:\n"
            "• Unlimited messages\n"
            "• Priority processing\n"
            "• Advanced stats\n"
            "• Priority support\n\n"
            "Visit: https://lucide.ai/pricing\n"
            "Or contact: support@lucide.ai",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif callback_data == "sub_enterprise":
        await query.edit_message_text(
            "🏢 **Enterprise Inquiry**\n\n"
            "For enterprise features and custom pricing,\n"
            "please contact: enterprise@lucide.ai",
            parse_mode=ParseMode.MARKDOWN,
        )


async def _handle_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle command shortcuts from inline keyboards."""
    from backend.telegram.handlers import command_handlers

    query = update.callback_query
    callback_data = query.data

    # Map callbacks to command handlers
    if callback_data == "cmd_context":
        await command_handlers.context_command(update, context)
    elif callback_data == "cmd_help":
        await command_handlers.help_command(update, context)
    elif callback_data == "cmd_language":
        await command_handlers.language_command(update, context)
    elif callback_data == "cmd_subscription":
        await command_handlers.subscription_command(update, context)
