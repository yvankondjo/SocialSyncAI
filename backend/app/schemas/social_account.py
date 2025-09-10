from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class SocialAccountBase(BaseModel):
    platform: str
    username: str
    account_id: str
    display_name: Optional[str] = None
    profile_url: Optional[HttpUrl] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    is_active: bool = True
    user_id: str


class SocialAccountCreate(SocialAccountBase):
    pass

class SocialAccount(SocialAccountBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: int
    
class AuthURL(BaseModel):
    authorization_url: HttpUrl


class SocialAccountWithStatus(SocialAccount):
    status: Optional[str] = None
    authorization_url: Optional[HttpUrl] = None


class AddAccountRequest(BaseModel):
    platform: str


class AddAccountResponse(BaseModel):
    platform: str
    status: str
    authorization_url: Optional[HttpUrl] = None