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
    post_id: str
    platform_comment_id: str
    parent_id: Optional[str] = None
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
    post_id: str
    platform_comment_id: str
    parent_id: Optional[str] = None
    author_name: Optional[str] = None
    author_id: Optional[str] = None
    text: str
    triage: Optional[AIDecision] = None
    ai_decision_id: Optional[str] = None
    hidden: bool
    replied_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

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
    post_id: str
    last_cursor: Optional[str] = None
    last_seen_ts: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCheckpointUpdate(BaseModel):
    """Schema for updating checkpoint"""
    last_cursor: Optional[str] = None
    last_seen_ts: Optional[datetime] = None
