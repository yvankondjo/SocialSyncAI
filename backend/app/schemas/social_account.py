from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.common import SocialPlatform

class SocialAccountBase(BaseModel):
    platform: SocialPlatform
    account_id: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    is_active: bool = True

class SocialAccountCreate(SocialAccountBase):
    organization_id: str

class SocialAccountUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    is_active: Optional[bool] = None

class SocialAccount(SocialAccountBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 