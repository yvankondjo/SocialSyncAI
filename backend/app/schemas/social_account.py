from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from enum import Enum

class PlatformStatus(str, Enum):
    CONNECTED = "connected"
    EXPIRED = "expired"
    PENDING_SETUP = "pending_setup"
    ERROR = "error"

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
    status: Optional[PlatformStatus] = PlatformStatus.CONNECTED
    status_message: Optional[str] = None


class SocialAccountCreate(SocialAccountBase):
    pass

class SocialAccount(SocialAccountBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SocialAccountWithStatus(BaseModel):
    id: Optional[str] = None
    platform: str
    username: Optional[str] = None
    account_id: Optional[str] = None
    display_name: Optional[str] = None
    profile_url: Optional[HttpUrl] = None
    status: PlatformStatus
    status_message: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SocialAccountsResponse(BaseModel):
    accounts: list[SocialAccountWithStatus]
    total: int

class ConnectAccountRequest(BaseModel):
    platform: str
    
class TokenData(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: int
    
class AuthURL(BaseModel):
    authorization_url: HttpUrl 