"""
Lucide Telegram Bot Application

Main bot application that sets up handlers, commands, and webhook integration.
"""
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    filters,
)

from backend.telegram.config import telegram_settings
from backend.telegram.handlers import (
    message_handlers,
    command_handlers,
    callback_handlers,
    inline_handlers,
)
from backend.telegram.middleware.rate_limiter import RateLimiter
from backend.telegram.middleware import error_handler
from backend.telegram.services.user_service import UserService
from backend.telegram.services.conversation_service import ConversationService
from backend.db.database import SessionLocal

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, telegram_settings.LOG_LEVEL),
)
logger = logging.getLogger(__name__)


class LucideTelegramBot:
    """Main Telegram bot application for Lucide."""

    def __init__(self):
        """Initialize the Telegram bot application."""
        self.application: Application = None
        self.rate_limiter = RateLimiter()
        self.user_service = UserService(SessionLocal)
        self.conversation_service = ConversationService(SessionLocal)
        logger.info("Lucide Telegram Bot initialized")

    def _register_handlers(self):
        """Register all command, message, and callback handlers."""
        logger.info("Registering handlers...")

        # Command handlers
        self.application.add_handler(
            CommandHandler("start", command_handlers.start_command)
        )
        self.application.add_handler(
            CommandHandler("help", command_handlers.help_command)
        )
        self.application.add_handler(
            CommandHandler("new", command_handlers.new_conversation_command)
        )
        self.application.add_handler(
            CommandHandler("history", command_handlers.history_command)
        )
        self.application.add_handler(
            CommandHandler("context", command_handlers.context_command)
        )
        self.application.add_handler(
            CommandHandler("language", command_handlers.language_command)
        )
        self.application.add_handler(
            CommandHandler("subscription", command_handlers.subscription_command)
        )
        self.application.add_handler(
            CommandHandler("settings", command_handlers.settings_command)
        )
        self.application.add_handler(
            CommandHandler("link", command_handlers.link_account_command)
        )
        self.application.add_handler(
            CommandHandler("export", command_handlers.export_data_command)
        )
        self.application.add_handler(
            CommandHandler("cancel", command_handlers.cancel_command)
        )

        # Callback query handlers (for inline keyboards)
        self.application.add_handler(
            CallbackQueryHandler(callback_handlers.handle_callback_query)
        )

        # Inline query handlers (for @LucideBot queries in any chat)
        if telegram_settings.TELEGRAM_ENABLE_INLINE_MODE:
            self.application.add_handler(
                InlineQueryHandler(inline_handlers.handle_inline_query)
            )

        # Message handlers (must be last)
        # Text messages (non-commands)
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                message_handlers.handle_text_message,
            )
        )

        # Group chat messages (only when bot is mentioned)
        if telegram_settings.TELEGRAM_ENABLE_GROUPS:
            self.application.add_handler(
                MessageHandler(
                    filters.ChatType.GROUPS & filters.TEXT,
                    message_handlers.handle_group_message,
                )
            )

        # Error handler
        self.application.add_error_handler(error_handler.handle_error)

        logger.info("Handlers registered successfully")

    async def _set_bot_commands(self):
        """Set bot commands menu (shown when user types /)."""
        commands = [
            BotCommand("start", "Start the bot and create account"),
            BotCommand("new", "Start a new conversation"),
            BotCommand("history", "View conversation history"),
            BotCommand("context", "Set match/league/team context"),
            BotCommand("language", "Switch language (FR/EN)"),
            BotCommand("subscription", "View subscription & upgrade"),
            BotCommand("settings", "Manage preferences"),
            BotCommand("export", "Export your data (GDPR)"),
            BotCommand("help", "Show help message"),
        ]

        await self.application.bot.set_my_commands(commands)
        logger.info("Bot commands menu set successfully")

    async def post_init(self, application: Application):
        """Post-initialization callback."""
        await self._set_bot_commands()
        logger.info("Bot post-initialization complete")

    async def post_shutdown(self, application: Application):
        """Post-shutdown callback."""
        logger.info("Bot shutting down...")
        # Close database sessions, cleanup resources
        await self.user_service.close()
        await self.conversation_service.close()

    def build_application(self) -> Application:
        """Build and configure the Telegram application."""
        logger.info("Building Telegram application...")

        # Create application
        builder = Application.builder()
        builder.token(telegram_settings.TELEGRAM_BOT_TOKEN)

        # Add post_init and post_shutdown callbacks
        builder.post_init(self.post_init)
        builder.post_shutdown(self.post_shutdown)

        self.application = builder.build()

        # Register all handlers
        self._register_handlers()

        logger.info("Telegram application built successfully")
        return self.application

    def run_polling(self):
        """Run the bot using long polling (for development)."""
        if not self.application:
            self.build_application()

        logger.info("Starting bot with polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    def run_webhook(self, host: str = "0.0.0.0", port: int = 8443):
        """Run the bot using webhooks (for production)."""
        if not self.application:
            self.build_application()

        if not telegram_settings.TELEGRAM_WEBHOOK_URL:
            raise ValueError("TELEGRAM_WEBHOOK_URL must be set for webhook mode")

        logger.info(f"Starting bot with webhook: {telegram_settings.TELEGRAM_WEBHOOK_URL}")
        logger.info(f"Listening on {host}:{port}")

        self.application.run_webhook(
            listen=host,
            port=port,
            url_path=telegram_settings.TELEGRAM_WEBHOOK_PATH,
            webhook_url=f"{telegram_settings.TELEGRAM_WEBHOOK_URL}{telegram_settings.TELEGRAM_WEBHOOK_PATH}",
            secret_token=telegram_settings.TELEGRAM_WEBHOOK_SECRET,
        )


def create_bot() -> LucideTelegramBot:
    """Factory function to create and configure the bot."""
    return LucideTelegramBot()


# For running directly
if __name__ == "__main__":
    bot = create_bot()
    bot.run_polling()  # Use polling for development
