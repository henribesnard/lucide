"""
Export Service for Telegram Bot

Handles user data export for GDPR compliance.
"""
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from backend.db.models import User, Conversation, Message

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting user data."""

    def __init__(self, db_session_factory):
        """Initialize ExportService."""
        self.db_session_factory = db_session_factory
        self._db_session = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if not self._db_session:
            self._db_session = self.db_session_factory()
        return self._db_session

    async def export_user_data(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Export all user data in GDPR-compliant format.

        Args:
            user_id: User's UUID

        Returns:
            Dictionary containing all user data
        """
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()

            if not user:
                raise ValueError(f"User not found: {user_id}")

            # Get all conversations
            conversations = (
                self.db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .all()
            )

            # Build export data
            export_data = {
                "user_profile": {
                    "user_id": str(user.user_id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "subscription_tier": user.subscription_tier.value,
                    "subscription_status": user.subscription_status.value,
                    "preferred_language": user.preferred_language,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat()
                    if user.last_login
                    else None,
                },
                "conversations": [
                    {
                        "conversation_id": str(conv.conversation_id),
                        "title": conv.title,
                        "created_at": conv.created_at.isoformat(),
                        "updated_at": conv.updated_at.isoformat(),
                        "messages": [
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "intent": msg.intent,
                                "tools_used": msg.tools_used,
                                "created_at": msg.created_at.isoformat(),
                            }
                            for msg in conv.messages
                        ],
                    }
                    for conv in conversations
                ],
                "statistics": {
                    "total_conversations": len(conversations),
                    "total_messages": sum(
                        len(conv.messages) for conv in conversations
                    ),
                },
                "export_metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "export_version": "1.0",
                    "gdpr_compliant": True,
                },
            }

            logger.info(f"Exported data for user {user_id}")
            return export_data

        except Exception as e:
            logger.error(f"Error exporting user data: {e}", exc_info=True)
            raise

    async def close(self):
        """Close database session."""
        if self._db_session:
            self._db_session.close()
            self._db_session = None
