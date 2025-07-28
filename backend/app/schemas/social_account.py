from pydantic import BaseModel, HttpUrl
from typing import Optional

class SocialAccountBase(BaseModel):
    platform: str
    username: str

class SocialAccountCreate(SocialAccountBase):
    pass

class SocialAccount(SocialAccountBase):
    id: str
    user_id: str

    class Config:
        orm_mode = True

class TokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    
class AuthURL(BaseModel):
    authorization_url: HttpUrl 