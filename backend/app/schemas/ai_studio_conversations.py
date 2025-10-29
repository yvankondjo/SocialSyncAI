"""
AI Studio Conversations Schemas
Pydantic models for AI Studio conversation metadata
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class ConversationMetadataBase(BaseModel):
    """Base schema for conversation metadata"""
    thread_id: str = Field(..., description="LangGraph thread ID")
    title: str = Field(..., description="Conversation title")
    model: str = Field(..., description="Model used for this conversation")
    message_count: int = Field(default=0, ge=0, description="Number of messages")


class ConversationMetadataCreate(ConversationMetadataBase):
    """Schema for creating conversation metadata"""
    pass


class ConversationMetadataUpdate(BaseModel):
    """Schema for updating conversation metadata"""
    title: Optional[str] = None
    message_count: Optional[int] = Field(None, ge=0)


class ConversationMetadata(ConversationMetadataBase):
    """Schema for conversation metadata response"""
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageItem(BaseModel):
    """Schema for a single message in a conversation"""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, description="Additional metadata (scheduled_posts, previews, etc.)")


class ConversationMessages(BaseModel):
    """Schema for conversation messages response"""
    thread_id: str
    messages: List[MessageItem]
    total_messages: int


class ConversationListResponse(BaseModel):
    """Schema for list of conversations"""
    conversations: List[ConversationMetadata]
    total: int
