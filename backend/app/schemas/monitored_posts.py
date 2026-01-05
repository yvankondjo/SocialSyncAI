"""
Pydantic schemas for Monitored Posts feature
Schemas for monitoring comments on all posts (scheduled + imported)
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class MonitoredPostBase(BaseModel):
    """Base schema for monitored post"""
    platform_post_id: str = Field(..., description="Platform-specific post ID")
    platform: Literal['instagram', 'facebook', 'twitter'] = Field(..., description="Social media platform")
    caption: Optional[str] = Field(None, description="Post caption/text")
    media_url: Optional[str] = Field(None, description="URL to post media (image/video)")
    posted_at: datetime = Field(..., description="When the post was published")


class MonitoredPostCreate(MonitoredPostBase):
    """Schema for creating a monitored post"""
    social_account_id: str = Field(..., description="UUID of social_accounts")
    source: Literal['scheduled', 'imported', 'manual'] = Field(..., description="Origin of the post")


class MonitoredPostInDB(MonitoredPostBase):
    """Schema for monitored post in database"""
    id: str
    user_id: str
    social_account_id: str
    source: Literal['scheduled', 'imported', 'manual']
    monitoring_enabled: bool
    monitoring_started_at: Optional[datetime] = None
    monitoring_ends_at: Optional[datetime] = None
    last_check_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Computed fields (from joins)
    comments_count: Optional[int] = None
    days_remaining: Optional[int] = None

    class Config:
        from_attributes = True


class MonitoredPostListResponse(BaseModel):
    """Response for listing monitored posts with pagination"""
    posts: list[MonitoredPostInDB]
    total: int
    limit: int
    offset: int


class MonitoringRulesBase(BaseModel):
    """Base schema for monitoring rules"""
    auto_monitor_enabled: bool = Field(True, description="Enable automatic monitoring of latest posts")
    auto_monitor_count: int = Field(5, ge=1, le=20, description="Number of latest posts to auto-monitor")
    monitoring_duration_days: int = Field(7, ge=1, le=30, description="How many days to monitor each post")
    ai_enabled_for_comments: bool = Field(True, description="Enable AI processing and auto-replies for comments")


class MonitoringRulesInDB(MonitoringRulesBase):
    """Schema for monitoring rules in database"""
    id: str
    user_id: str
    social_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncInstagramPostsRequest(BaseModel):
    """Request schema for syncing Instagram posts"""
    social_account_id: Optional[str] = Field(None, description="Specific account to sync (optional)")
    limit: int = Field(50, ge=1, le=100, description="Max number of posts to import")


class SyncInstagramPostsResponse(BaseModel):
    """Response schema for sync operation"""
    success: bool
    posts_imported: int
    posts_monitored: int
    message: str


class ToggleMonitoringRequest(BaseModel):
    """Request schema for toggling monitoring"""
    duration_days: Optional[int] = Field(None, ge=1, le=30, description="Custom monitoring duration")


class ToggleMonitoringResponse(BaseModel):
    """Response schema for toggle operation"""
    success: bool
    post: MonitoredPostInDB
    message: str
