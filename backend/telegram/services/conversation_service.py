"""
Conversation Service for Telegram Bot

Handles conversation CRUD operations.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from backend.db.models import Conversation, Message

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations."""

    def __init__(self, db_session_factory):
        """
        Initialize ConversationService.

        Args:
            db_session_factory: SQLAlchemy session factory
        """
        self.db_session_factory = db_session_factory
        self._db_session: Optional[Session] = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if not self._db_session:
            self._db_session = self.db_session_factory()
        return self._db_session

    async def create_conversation(
        self, conversation_id: str, user_id: uuid.UUID, title: str
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            conversation_id: UUID string for the conversation
            user_id: User's UUID
            title: Conversation title

        Returns:
            Created Conversation object
        """
        try:
            conversation = Conversation(
                conversation_id=uuid.UUID(conversation_id),
                user_id=user_id,
                title=title,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)

            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating conversation: {e}", exc_info=True)
            raise

    async def get_user_conversations(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> List[Conversation]:
        """
        Get user's conversations ordered by most recent.

        Args:
            user_id: User's UUID
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        try:
            conversations = (
                self.db.query(Conversation)
                .filter(
                    Conversation.user_id == user_id,
                    Conversation.is_deleted == False,
                )
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
                .all()
            )

            return conversations

        except Exception as e:
            logger.error(f"Error fetching conversations: {e}", exc_info=True)
            return []

    async def get_conversation(
        self, conversation_id: str
    ) -> Optional[Conversation]:
        """
        Get a specific conversation.

        Args:
            conversation_id: Conversation UUID string

        Returns:
            Conversation object or None if not found
        """
        try:
            return (
                self.db.query(Conversation)
                .filter(
                    Conversation.conversation_id == uuid.UUID(conversation_id),
                    Conversation.is_deleted == False,
                )
                .first()
            )

        except Exception as e:
            logger.error(f"Error fetching conversation: {e}", exc_info=True)
            return None

    async def update_conversation_title(
        self, conversation_id: str, title: str
    ) -> bool:
        """
        Update conversation title.

        Args:
            conversation_id: Conversation UUID string
            title: New title

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = (
                self.db.query(Conversation)
                .filter(Conversation.conversation_id == uuid.UUID(conversation_id))
                .first()
            )

            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return False

            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Updated title for conversation {conversation_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating conversation title: {e}", exc_info=True)
            return False

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Soft-delete a conversation.

        Args:
            conversation_id: Conversation UUID string

        Returns:
            True if successful, False otherwise
        """
        try:
            conversation = (
                self.db.query(Conversation)
                .filter(Conversation.conversation_id == uuid.UUID(conversation_id))
                .first()
            )

            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return False

            conversation.is_deleted = True
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Deleted conversation {conversation_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting conversation: {e}", exc_info=True)
            return False

    async def close(self):
        """Close database session."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None
