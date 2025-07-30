from pydantic import BaseModel, Json
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from .common import SocialPlatform

class AnalyticsBase(BaseModel):
    likes: Optional[int] = 0
    shares: Optional[int] = 0
    comments: Optional[int] = 0
    impressions: Optional[int] = 0
    reach: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    clicks: Optional[int] = 0
    conversions: Optional[int] = 0
    raw_metrics: Optional[Dict[str, Any]] = None

class AnalyticsCreate(AnalyticsBase):
    content_id: UUID
    platform: SocialPlatform

class Analytics(AnalyticsCreate):
    id: UUID
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsHistory(AnalyticsBase):
    id: UUID
    recorded_at: datetime
    created_at: datetime
    user_id: UUID

    class Config:
        from_attributes = True 