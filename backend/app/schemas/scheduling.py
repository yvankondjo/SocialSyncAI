from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PlatformType(str, Enum):
    INSTAGRAM = "instagram"
    REDDIT = "reddit"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"

class PostStatus(str, Enum):
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PlatformPreview(BaseModel):
    platform: PlatformType
    preview_data: Dict[str, Any]
    character_count: int
    character_limit: int
    is_valid: bool
    validation_errors: List[str] = []

class SchedulePostRequest(BaseModel):
    content: str = Field(..., max_length=5000)
    platforms: List[PlatformType] = Field(..., min_items=1)
    scheduled_at: datetime
    media_urls: Optional[List[str]] = []
    post_type: str = "text"
    metadata: Optional[Dict[str, Any]] = {}
    
    @validator('scheduled_at')
    def validate_future_date(cls, v):
        if v <= datetime.now():
            raise ValueError('La date de planification doit être dans le futur')
        return v
    
    @validator('platforms')
    def validate_platforms(cls, v):
        if PlatformType.LINKEDIN in v:
            raise ValueError('LinkedIn n\'est pas encore disponible pour la planification')
        return v

class PostPreviewRequest(BaseModel):
    content: str = Field(..., max_length=5000)
    platforms: List[PlatformType] = Field(..., min_items=1)
    media_urls: Optional[List[str]] = []
    post_type: str = "text"

class PostPreviewResponse(BaseModel):
    previews: List[PlatformPreview]
    global_validation: Dict[str, Any]

class ScheduledPost(BaseModel):
    id: str
    user_id: str
    content: str
    platforms: List[str]
    scheduled_at: datetime
    status: PostStatus
    media_urls: Optional[List[str]] = []
    post_type: str
    metadata: Optional[Dict[str, Any]] = {}
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class SchedulePostResponse(BaseModel):
    post: ScheduledPost
    message: str = "Post planifié avec succès"

class CalendarPostsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    platforms: Optional[List[PlatformType]] = None

class CalendarPostsResponse(BaseModel):
    posts: List[ScheduledPost]
    total: int