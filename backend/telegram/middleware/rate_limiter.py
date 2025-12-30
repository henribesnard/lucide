"""
Rate Limiter Middleware

Prevents users from spamming the bot with too many requests.
"""
import time
import logging
from functools import wraps
from typing import Dict, List
from telegram import Update
from telegram.ext import ContextTypes

from backend.telegram.config import telegram_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Tracks message counts per user within a time window.
    For production, consider using Redis for distributed rate limiting.
    """

    def __init__(
        self,
        max_messages: int = None,
        window_seconds: int = None,
    ):
        """
        Initialize rate limiter.

        Args:
            max_messages: Maximum messages allowed per window
            window_seconds: Time window in seconds
        """
        self.max_messages = max_messages or telegram_settings.TELEGRAM_RATE_LIMIT_MESSAGES
        self.window_seconds = window_seconds or telegram_settings.TELEGRAM_RATE_LIMIT_WINDOW

        # Store: {user_id: [timestamp1, timestamp2, ...]}
        self.user_timestamps: Dict[int, List[float]] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        """
        Check if user is rate limited.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user should be rate limited, False otherwise
        """
        now = time.time()
        cutoff_time = now - self.window_seconds

        # Get user's timestamps
        if user_id not in self.user_timestamps:
            self.user_timestamps[user_id] = []

        # Remove old timestamps
        self.user_timestamps[user_id] = [
            ts for ts in self.user_timestamps[user_id] if ts > cutoff_time
        ]

        # Check limit
        if len(self.user_timestamps[user_id]) >= self.max_messages:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{len(self.user_timestamps[user_id])} messages in {self.window_seconds}s"
            )
            return True

        # Record this request
        self.user_timestamps[user_id].append(now)
        return False

    def get_retry_after(self, user_id: int) -> int:
        """
        Get seconds until user can send another message.

        Args:
            user_id: Telegram user ID

        Returns:
            Seconds to wait
        """
        if user_id not in self.user_timestamps or not self.user_timestamps[user_id]:
            return 0

        oldest_timestamp = min(self.user_timestamps[user_id])
        now = time.time()
        time_since_oldest = now - oldest_timestamp

        if time_since_oldest >= self.window_seconds:
            return 0

        return int(self.window_seconds - time_since_oldest)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_per_minute: int = 30):
    """
    Decorator for rate limiting handler functions.

    Args:
        max_per_minute: Maximum messages per minute

    Usage:
        @rate_limit(max_per_minute=30)
        async def my_handler(update, context):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id

            # Check rate limit
            if _rate_limiter.is_rate_limited(user_id):
                retry_after = _rate_limiter.get_retry_after(user_id)

                await update.message.reply_text(
                    f"⚠️ **Rate Limit Exceeded**\n\n"
                    f"You're sending messages too quickly.\n"
                    f"Please wait {retry_after} seconds and try again.\n\n"
                    f"**Limit:** {_rate_limiter.max_messages} messages per minute\n\n"
                    f"Upgrade to Premium for higher limits: /subscription",
                    parse_mode="Markdown",
                )
                return

            # Proceed with handler
            return await func(update, context)

        return wrapper

    return decorator
