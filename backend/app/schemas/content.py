from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ContentBase(BaseModel):
    title: str
    content: str
    content_type: Optional[str] = 'text'
    status: Optional[str] = 'draft'
    media_url: Optional[str] = None

class ContentCreate(ContentBase):
    social_account_id: UUID

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class Content(ContentBase):
    id: UUID
    social_account_id: UUID
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None

    class Config:
        orm_mode = True 