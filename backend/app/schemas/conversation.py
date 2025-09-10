from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Conversation(BaseModel):
    id: str
    social_account_id: str
    external_conversation_id: Optional[str] = None
    customer_identifier: str = Field(..., description="Phone number or Instagram user ID")
    customer_name: Optional[str] = None
    customer_avatar_url: Optional[str] = None
    status: str = "open"
    priority: str = "normal"
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    automation_disabled: bool = False
    created_at: datetime
    updated_at: datetime

    # Champs dérivés pour la compatibilité frontend
    channel: Optional[str] = None
    last_message_snippet: Optional[str] = None

    class Config:
        from_attributes = True

class Message(BaseModel):
    id: str
    conversation_id: str
    external_message_id: Optional[str] = None
    direction: str = Field(..., description="inbound or outbound")
    message_type: str = "text"
    content: str
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_avatar_url: Optional[str] = None
    status: str = "sent"
    is_from_agent: bool = False
    agent_id: Optional[str] = None
    reply_to_message_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    social_account_id: str
    customer_identifier: str
    customer_name: Optional[str] = None
    external_conversation_id: Optional[str] = None

class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"
    media_url: Optional[str] = None
    media_type: Optional[str] = None

class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"
    media_url: Optional[str] = None
    media_type: Optional[str] = None

class ConversationListResponse(BaseModel):
    conversations: List[Conversation]
    total: int

class MessageListResponse(BaseModel):
    messages: List[Message]
    total: int

class ConversationQueryParams(BaseModel):
    channel: Optional[str] = None
    status: Optional[str] = None
    limit: int = Field(default=50, le=100)
    offset: int = Field(default=0, ge=0)