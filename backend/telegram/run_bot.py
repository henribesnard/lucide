"""
Simple script to run the Telegram bot.

Usage:
    python backend/telegram/run_bot.py [--webhook]

Options:
    --webhook    Run in webhook mode (production)
                 Default: polling mode (development)
"""
import sys
import argparse
import logging

from backend.telegram.bot import create_bot

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for running the bot."""
    parser = argparse.ArgumentParser(description="Run Lucide Telegram Bot")
    parser.add_argument(
        "--webhook",
        action="store_true",
        help="Run in webhook mode (default: polling)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to listen on (webhook mode only)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8443,
        help="Port to listen on (webhook mode only)",
    )

    args = parser.parse_args()

    # Create bot instance
    bot = create_bot()

    if args.webhook:
        logger.info("Starting bot in WEBHOOK mode...")
        logger.info(f"Listening on {args.host}:{args.port}")
        bot.run_webhook(host=args.host, port=args.port)
    else:
        logger.info("Starting bot in POLLING mode...")
        logger.info("Press Ctrl+C to stop")
        bot.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
