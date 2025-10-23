"""
Pydantic schemas for Comments feature
Schemas for public comments on scheduled posts
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.ai_rules import AIDecision


class CommentBase(BaseModel):
    """Base schema for comment"""
    text: str
    author_name: Optional[str] = None
    author_id: Optional[str] = None


class CommentCreate(CommentBase):
    """Schema for creating a comment"""
    post_id: Optional[str] = None  # Legacy FK to scheduled_posts (backwards compatibility)
    monitored_post_id: Optional[str] = None  # Primary FK to monitored_posts
    platform_comment_id: str
    parent_id: Optional[str] = None  # Instagram parent comment ID (TEXT)
    like_count: int = 0
    created_at: datetime


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    triage: Optional[AIDecision] = None
    ai_decision_id: Optional[str] = None
    hidden: Optional[bool] = None
    replied_at: Optional[datetime] = None


class CommentInDB(BaseModel):
    """Schema for comment in database"""
    id: str
    post_id: Optional[str] = None  # Legacy FK (nullable for new comments)
    monitored_post_id: Optional[str] = None  # Primary FK to monitored_posts
    platform_comment_id: str
    parent_id: Optional[str] = None  # Instagram parent comment ID (TEXT)
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    text: str
    triage: Optional[AIDecision] = None
    ai_decision_id: Optional[str] = None
    hidden: bool = False
    replied_at: Optional[datetime] = None
    ai_reply_text: Optional[str] = None  # Store the AI-generated reply
    like_count: int = 0  # Number of likes from Instagram
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed fields from monitored_posts join
    post_caption: Optional[str] = None
    post_platform: Optional[str] = None

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Response for listing comments with pagination"""
    comments: List[CommentInDB]
    total: int
    limit: int
    offset: int


class CommentCheckpoint(BaseModel):
    """Schema for comment checkpoint (pagination state)"""
    post_id: Optional[str] = None  # Legacy FK (nullable)
    monitored_post_id: Optional[str] = None  # Primary FK to monitored_posts
    last_cursor: Optional[str] = None
    last_seen_ts: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CommentCheckpointUpdate(BaseModel):
    """Schema for updating checkpoint"""
    last_cursor: Optional[str] = None
    last_seen_ts: Optional[datetime] = None
