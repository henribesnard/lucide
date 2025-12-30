"""
User Service for Telegram Bot

Handles user authentication, creation, and management for Telegram users.

NOTE: This service assumes the User model has been extended with Telegram fields:
- telegram_id (BigInt, unique, indexed)
- telegram_username (String)
- telegram_first_name (String)
- telegram_last_name (String)
- telegram_language_code (String)

These fields need to be added via database migration.
"""
import logging
from typing import Optional
from datetime import datetime
from telegram import User as TelegramUser
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.db.models import User, SubscriptionTier, SubscriptionStatus
import uuid

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing Telegram users."""

    def __init__(self, db_session_factory):
        """
        Initialize UserService.

        Args:
            db_session_factory: SQLAlchemy session factory (e.g., SessionLocal)
        """
        self.db_session_factory = db_session_factory
        self._db_session: Optional[Session] = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if not self._db_session:
            self._db_session = self.db_session_factory()
        return self._db_session

    async def get_or_create_user(self, telegram_user: TelegramUser) -> User:
        """
        Get existing user by Telegram ID or create a new one.

        Args:
            telegram_user: Telegram User object from update.effective_user

        Returns:
            User database model instance

        Note:
            This method requires telegram_id field in User model.
            For now, it creates users with telegram_id as a workaround.
        """
        try:
            # Try to find user by telegram_id
            # NOTE: This assumes telegram_id field exists
            # For backwards compatibility, we'll store telegram_id in email temporarily
            email_fallback = f"telegram_{telegram_user.id}@lucide.telegram"

            user = self.db.query(User).filter(User.email == email_fallback).first()

            if user:
                # Update last login
                user.last_login = datetime.utcnow()
                self.db.commit()
                logger.info(f"Found existing user for Telegram ID {telegram_user.id}")
                return user

            # Create new user
            logger.info(f"Creating new user for Telegram ID {telegram_user.id}")

            new_user = User(
                user_id=uuid.uuid4(),
                email=email_fallback,  # Temporary: use telegram ID as email
                password_hash="telegram_auth",  # No password for Telegram users
                first_name=telegram_user.first_name or "Telegram",
                last_name=telegram_user.last_name or "User",
                is_active=True,
                is_verified=True,  # Auto-verify Telegram users
                is_superuser=False,
                subscription_tier=SubscriptionTier.FREE,
                subscription_status=SubscriptionStatus.ACTIVE,
                preferred_language=telegram_user.language_code[:2]
                if telegram_user.language_code
                else "fr",
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                # TODO: Set these fields when migration is done:
                # telegram_id=telegram_user.id,
                # telegram_username=telegram_user.username,
                # telegram_first_name=telegram_user.first_name,
                # telegram_last_name=telegram_user.last_name,
                # telegram_language_code=telegram_user.language_code,
            )

            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            logger.info(
                f"Created new user: {new_user.user_id} (Telegram: {telegram_user.id})"
            )

            return new_user

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            # Try to fetch again in case of race condition
            return self.db.query(User).filter(User.email == email_fallback).first()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in get_or_create_user: {e}", exc_info=True)
            raise

    async def update_language(self, user_id: uuid.UUID, language_code: str) -> bool:
        """
        Update user's preferred language.

        Args:
            user_id: User's UUID
            language_code: Language code ('fr' or 'en')

        Returns:
            True if successful, False otherwise
        """
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()

            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            user.preferred_language = language_code
            user.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated language for user {user_id} to {language_code}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating language: {e}", exc_info=True)
            return False

    async def track_conversion(self, user_id: uuid.UUID, source: str) -> None:
        """
        Track user conversion source (e.g., from deep link).

        Args:
            user_id: User's UUID
            source: Conversion source (e.g., 'web_campaign', 'referral')
        """
        # TODO: Implement conversion tracking
        # This could be stored in a separate conversions table
        logger.info(f"Conversion tracked: User {user_id} from source {source}")

    async def link_account(
        self, telegram_user: TelegramUser, linking_code: str
    ) -> bool:
        """
        Link Telegram account to existing web/mobile account.

        Args:
            telegram_user: Telegram User object
            linking_code: Linking code from web/mobile app (e.g., LUCIDE-ABC123)

        Returns:
            True if successful, False if code is invalid/expired
        """
        # TODO: Implement account linking
        # 1. Verify linking code in Redis
        # 2. Get user_id from code
        # 3. Update user record with telegram_id
        # 4. Delete linking code from Redis

        logger.info(
            f"Account linking requested: {telegram_user.id} with code {linking_code}"
        )

        # Placeholder implementation
        return False

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get user by UUID.

        Args:
            user_id: User's UUID

        Returns:
            User object or None if not found
        """
        try:
            return self.db.query(User).filter(User.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error fetching user: {e}", exc_info=True)
            return None

    async def close(self):
        """Close database session."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None
