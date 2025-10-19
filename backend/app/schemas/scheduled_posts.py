"""
Pydantic schemas for Scheduled Posts feature
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Supported platforms"""
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    """Post status values"""
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunStatus(str, Enum):
    """Execution run status"""
    SUCCESS = "success"
    FAILED = "failed"


class MediaItem(BaseModel):
    """Media item in post content"""
    type: str = Field(..., description="Media type: image, video, audio")
    url: str = Field(..., description="URL to media file")
    caption: Optional[str] = None


class PostContent(BaseModel):
    """Post content structure"""
    text: Optional[str] = None
    media: List[MediaItem] = Field(default_factory=list)

    @field_validator('text', 'media')
    @classmethod
    def validate_content(cls, v, info):
        """At least text or media must be provided"""
        # This will be called for each field, so we check in the model validator instead
        return v

    def model_post_init(self, __context):
        """Validate that at least text or media is provided"""
        if not self.text and not self.media:
            raise ValueError("Post must have either text or media content")


class ScheduledPostCreate(BaseModel):
    """Schema for creating a scheduled post"""
    channel_id: str = Field(..., description="UUID of social_accounts")
    content: PostContent = Field(..., description="Post content (text and/or media)")
    publish_at: datetime = Field(..., description="When to publish the post")
    rrule: Optional[str] = Field(None, description="iCal recurrence rule (optional)")

    @field_validator('publish_at')
    @classmethod
    def validate_publish_at(cls, v):
        """Ensure publish_at is in the future"""
        if v <= datetime.utcnow():
            raise ValueError("publish_at must be in the future")
        return v


class ScheduledPostUpdate(BaseModel):
    """Schema for updating a scheduled post"""
    content: Optional[PostContent] = None
    publish_at: Optional[datetime] = None
    rrule: Optional[str] = None
    status: Optional[PostStatus] = None

    @field_validator('publish_at')
    @classmethod
    def validate_publish_at(cls, v):
        """Ensure publish_at is in the future if provided"""
        if v and v <= datetime.utcnow():
            raise ValueError("publish_at must be in the future")
        return v


class ScheduledPostResponse(BaseModel):
    """Schema for scheduled post response"""
    id: str
    user_id: str
    channel_id: str
    platform: Platform
    content_json: Dict[str, Any]
    publish_at: datetime
    rrule: Optional[str]
    status: PostStatus
    platform_post_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    last_check_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    stop_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduledPostListResponse(BaseModel):
    """Response for listing scheduled posts with pagination"""
    posts: List[ScheduledPostResponse]
    total: int
    limit: int
    offset: int


class PostRunResponse(BaseModel):
    """Schema for post execution run"""
    id: str
    scheduled_post_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    status: RunStatus
    error: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PostRunListResponse(BaseModel):
    """Response for listing post runs"""
    runs: List[PostRunResponse]
    total: int
    limit: int
    offset: int


class PostStatistics(BaseModel):
    """Statistics for scheduled posts"""
    queued: int
    publishing: int
    published: int
    failed: int
    cancelled: int
    total: int
