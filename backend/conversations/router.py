import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.database import get_db
from backend.db.models import User, Conversation, Message
from backend.auth.dependencies import get_current_user
from backend.conversations.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation for the current user."""
    conversation = Conversation(
        user_id=current_user.user_id,
        title=request.title or "Nouvelle conversation",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    logger.info(f"Created conversation {conversation.conversation_id} for user {current_user.email}")

    return conversation


@router.get("", response_model=List[ConversationListResponse])
async def list_conversations(
    archived: Optional[bool] = Query(False, description="Filter archived conversations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversations for the current user."""
    query = db.query(
        Conversation,
        func.count(Message.message_id).label("message_count")
    ).outerjoin(Message).filter(
        Conversation.user_id == current_user.user_id,
        Conversation.is_deleted == False
    )

    if archived is not None:
        query = query.filter(Conversation.is_archived == archived)

    query = query.group_by(Conversation.conversation_id).order_by(Conversation.updated_at.desc())

    results = query.all()

    return [
        ConversationListResponse(
            conversation_id=conv.conversation_id,
            user_id=conv.user_id,
            title=conv.title,
            is_archived=conv.is_archived,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=count
        )
        for conv, count in results
    ]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.user_id == current_user.user_id,
        Conversation.is_deleted == False
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a conversation (title, archive status)."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.user_id == current_user.user_id,
        Conversation.is_deleted == False
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    if request.title is not None:
        conversation.title = request.title

    if request.is_archived is not None:
        conversation.is_archived = request.is_archived

    db.commit()
    db.refresh(conversation)

    logger.info(f"Updated conversation {conversation_id}")

    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id,
        Conversation.user_id == current_user.user_id,
        Conversation.is_deleted == False
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    conversation.is_deleted = True
    db.commit()

    logger.info(f"Deleted conversation {conversation_id}")

    return None
