"""
Error Handler Middleware

Handles errors and exceptions in the Telegram bot.
"""
import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler for the bot.

    Logs errors and sends user-friendly messages.

    Args:
        update: Telegram update object
        context: Bot context containing the error
    """
    # Log the error
    logger.error(
        f"Exception while handling update {update}: {context.error}",
        exc_info=context.error,
    )

    # Get traceback
    tb_string = "".join(
        traceback.format_exception(
            None, context.error, context.error.__traceback__
        )
    )
    logger.error(f"Traceback:\n{tb_string}")

    # Send user-friendly error message
    try:
        if update and update.effective_message:
            error_message = (
                "❌ **An error occurred**\n\n"
                "Sorry, something went wrong while processing your request.\n"
                "Our team has been notified.\n\n"
                "Please try again in a moment or contact support if the issue persists.\n\n"
                "Support: support@lucide.ai"
            )

            await update.effective_message.reply_text(
                error_message,
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(f"Error in error handler: {e}", exc_info=True)

    # TODO: Send error notification to admins
    # TODO: Log to external error tracking service (e.g., Sentry)


async def notify_admins(error: Exception, update: Update = None):
    """
    Notify administrators about critical errors.

    Args:
        error: The exception that occurred
        update: The update that caused the error (if available)
    """
    # TODO: Implement admin notification
    # This could send a message to an admin Telegram group/channel
    # or send an email to the dev team
    pass
