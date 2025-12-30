"""
Telegram Bot Message Handlers

Handles text messages from users and processes them through the Lucide pipeline.
"""
import logging
import time
import uuid
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode, ChatAction
from datetime import datetime

from backend.telegram.services.user_service import UserService
from backend.telegram.services.conversation_service import ConversationService
from backend.telegram.utils.formatter import MessageFormatter
from backend.telegram.middleware.rate_limiter import rate_limit
from backend.agents.pipeline import LucidePipeline
from backend.db.database import SessionLocal

logger = logging.getLogger(__name__)


@rate_limit(max_per_minute=30)
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle regular text messages from users.

    This is the main message handler that:
    1. Authenticates the user
    2. Creates/retrieves conversation
    3. Processes message through Lucide pipeline
    4. Streams response back to user
    """
    user = update.effective_user
    message_text = update.message.text

    logger.info(f"Received message from {user.id} ({user.username}): {message_text[:100]}")

    user_service = UserService(SessionLocal)
    conversation_service = ConversationService(SessionLocal)

    try:
        # Get or create user
        user_record = await user_service.get_or_create_user(user)

        # Get or create active conversation
        active_conversation_id = context.user_data.get("active_conversation_id")

        if not active_conversation_id:
            # Create new conversation
            active_conversation_id = str(uuid.uuid4())
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            await conversation_service.create_conversation(
                conversation_id=active_conversation_id,
                user_id=user_record.user_id,
                title=title,
            )

            context.user_data["active_conversation_id"] = active_conversation_id

        # Get user's context (league, match, team, player)
        user_context = context.user_data.get("context", None)

        # Send typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)

        # Get or determine language
        language = user_record.preferred_language or "fr"

        # Get or determine model type
        model_type = context.user_data.get("model_type", "slow")

        # Create status message for updates
        status_message = await update.message.reply_text(
            "⏳ Analyzing your question...",
            parse_mode=ParseMode.MARKDOWN,
        )

        # Create pipeline instance
        pipeline = LucidePipeline(
            session_id=active_conversation_id,
            db_session_factory=SessionLocal,
        )

        # Track statuses for streaming updates
        last_status_update = time.time()
        current_status = ""

        def status_callback(step: str, message: str):
            """Callback for pipeline status updates."""
            nonlocal current_status, last_status_update
            current_status = message
            logger.info(f"Pipeline status: {step} - {message}")

        # Process through pipeline
        logger.info(f"Processing message through pipeline (session: {active_conversation_id})")

        result = await pipeline.process(
            message_text,
            context=user_context,
            user_id=str(user_record.user_id),
            model_type=model_type,
            language=language,
            status_callback=status_callback,
        )

        resolved_context = result.get("context")
        if resolved_context:
            context.user_data["context"] = resolved_context

        # Delete status message
        try:
            await status_message.delete()
        except Exception:
            pass  # Message might be too old

        # Get response
        response_text = result["answer"]
        intent_obj = result["intent"]
        tool_names = [tool.name for tool in result["tool_results"]]

        # Format response for Telegram
        formatter = MessageFormatter()
        formatted_response = formatter.format_for_telegram(
            response_text,
            max_length=4096,  # Telegram's limit
        )

        # Send response (split if too long)
        response_messages = formatter.split_long_message(formatted_response)

        for i, msg_part in enumerate(response_messages):
            await update.message.reply_text(
                msg_part,
                parse_mode=ParseMode.MARKDOWN,
            )

            # Small delay between parts
            if i < len(response_messages) - 1:
                await update.message.chat.send_action(ChatAction.TYPING)
                import asyncio
                await asyncio.sleep(0.5)

        # Log intent and tools used
        logger.info(
            f"Response sent. Intent: {intent_obj.intent}, Tools: {', '.join(tool_names)}"
        )

        # Auto-update conversation title if it's the first message
        if message_text == update.message.text:  # First message in conversation
            smart_title = _generate_smart_title(message_text, resolved_context or user_context)
            if smart_title:
                await conversation_service.update_conversation_title(
                    conversation_id=active_conversation_id,
                    title=smart_title,
                )

    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ **An error occurred while processing your message.**\n\n"
            "Please try again or contact support if the issue persists.",
            parse_mode=ParseMode.MARKDOWN,
        )

    finally:
        await user_service.close()
        await conversation_service.close()


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle messages in group chats.

    Only responds when:
    - Bot is mentioned (@LucideBot)
    - Message is a reply to the bot's message
    """
    user = update.effective_user
    message_text = update.message.text

    # Check if bot is mentioned or if it's a reply to bot
    bot_username = context.bot.username
    is_mentioned = f"@{bot_username}" in message_text
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user.id == context.bot.id
    )

    if not is_mentioned and not is_reply_to_bot:
        return  # Ignore message

    logger.info(f"Group message from {user.id} in {update.effective_chat.id}: {message_text[:100]}")

    # Remove mention from message
    clean_message = message_text.replace(f"@{bot_username}", "").strip()

    # Process similarly to regular message
    user_service = UserService(SessionLocal)

    try:
        # Get or create user
        user_record = await user_service.get_or_create_user(user)

        # Use group-specific conversation ID
        group_conversation_id = f"group_{update.effective_chat.id}"

        # Send typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)

        # Create pipeline
        pipeline = LucidePipeline(
            session_id=group_conversation_id,
            db_session_factory=SessionLocal,
        )

        # Process message
        result = await pipeline.process(
            clean_message,
            context=None,  # No persistent context in groups
            user_id=str(user_record.user_id),
            model_type="slow",
            language=user_record.preferred_language or "fr",
        )

        response_text = result["answer"]

        # Format and send response
        formatter = MessageFormatter()
        formatted_response = formatter.format_for_telegram(response_text)

        # Reply in thread
        await update.message.reply_text(
            formatted_response,
            parse_mode=ParseMode.MARKDOWN,
        )

        logger.info(f"Group response sent to chat {update.effective_chat.id}")

    except Exception as e:
        logger.error(f"Error handling group message: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred. Please try again.",
            parse_mode=ParseMode.MARKDOWN,
        )

    finally:
        await user_service.close()


def _generate_smart_title(message: str, context: dict = None) -> str:
    """
    Generate a smart conversation title from the first message and context.

    Examples:
    - "CAN Gabon vs Mozambique: analyse"
    - "Ligue 1 PSG: statistiques"
    - "Premier League standings"
    """
    if not context:
        # Extract from message
        message_lower = message.lower()

        # Simple intent detection
        if any(word in message_lower for word in ["classement", "standings", "ranking"]):
            intent = ": classement"
        elif any(word in message_lower for word in ["statistique", "stats"]):
            intent = ": stats"
        elif any(word in message_lower for word in ["pronostic", "prediction", "prédire", "predict"]):
            intent = ": pronostic"
        elif any(word in message_lower for word in ["analys", "analyse"]):
            intent = ": analyse"
        else:
            intent = ""

        # Truncate message
        base = message[:40] + "..." if len(message) > 40 else message
        return base + intent

    # Build from context
    title_parts = []

    if "competition_name" in context:
        comp_name = context["competition_name"]
        # Shorten common names
        comp_name = comp_name.replace("Africa Cup of Nations", "CAN")
        comp_name = comp_name.replace("Premier League", "EPL")
        comp_name = comp_name.replace("UEFA Champions League", "LDC")
        title_parts.append(comp_name)
    elif "league_name" in context:
        title_parts.append(context["league_name"])

    if "team1_name" in context and "team2_name" in context:
        title_parts.append(f"{context['team1_name']} vs {context['team2_name']}")
    elif "team_name" in context:
        title_parts.append(context["team_name"])

    if "player_name" in context:
        title_parts.append(context["player_name"])

    # Add intent suffix
    message_lower = message.lower()
    if any(word in message_lower for word in ["analys", "analyse"]):
        intent_suffix = ": analyse"
    elif any(word in message_lower for word in ["stats", "statistique"]):
        intent_suffix = ": stats"
    elif any(word in message_lower for word in ["pronostic", "prédiction"]):
        intent_suffix = ": pronostic"
    else:
        intent_suffix = ""

    if title_parts:
        full_title = " ".join(title_parts) + intent_suffix
        if len(full_title) > 60:
            return full_title[:57] + "..."
        return full_title

    # Fallback
    return message[:50] + "..." if len(message) > 50 else message
