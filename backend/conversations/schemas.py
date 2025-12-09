from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    message_id: UUID
    conversation_id: UUID
    role: str
    content: str
    intent: Optional[str]
    tools_used: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_archived: Optional[bool] = None


class ConversationResponse(BaseModel):
    conversation_id: UUID
    user_id: UUID
    title: Optional[str]
    is_archived: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    conversation_id: UUID
    user_id: UUID
    title: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True
