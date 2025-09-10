from pydantic import BaseModel, HttpUrl, field_validator
from typing import Literal, Optional
from datetime import datetime

class ScheduledPostCreate(BaseModel):
    platform: Literal['instagram', 'reddit']
    social_account_id: str
    text: str
    media_url: Optional[HttpUrl] = None
    scheduled_at: datetime  # Interprété en Europe/Paris si naive

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Le texte du post est requis')
        return v

class ScheduledPost(BaseModel):
    id: str
    platform: str
    social_account_id: str
    text: str
    media_url: Optional[str] = None
    scheduled_at: datetime
    status: str

