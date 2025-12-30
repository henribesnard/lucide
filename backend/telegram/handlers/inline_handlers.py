"""
Telegram Bot Inline Query Handlers

Handles inline queries (when users type @LucideBot in any chat).
"""
import logging
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
import uuid

logger = logging.getLogger(__name__)


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle inline queries - when users type @LucideBot query in any chat.

    This allows users to search for matches, teams, or get quick predictions
    without opening the bot chat.

    Example: @LucideBot PSG vs Barcelona
    """
    query_text = update.inline_query.query

    if not query_text or len(query_text) < 3:
        # Show help/examples when query is empty
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Search for a match",
                description="Example: PSG vs Barcelona",
                input_message_content=InputTextMessageContent(
                    "Use @LucideBot followed by team names to search for matches"
                ),
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Get team standings",
                description="Example: Premier League standings",
                input_message_content=InputTextMessageContent(
                    "Use @LucideBot to get league standings"
                ),
            ),
        ]
        await update.inline_query.answer(results, cache_time=300)
        return

    logger.info(f"Inline query from {update.inline_query.from_user.id}: {query_text}")

    # TODO: Implement actual search
    # For now, return a placeholder
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Search: {query_text}",
            description="Tap to analyze with Lucide",
            input_message_content=InputTextMessageContent(
                f"Analyzing: {query_text}\n\n"
                f"(Open @LucideBot for full analysis)"
            ),
        )
    ]

    await update.inline_query.answer(results, cache_time=300)
