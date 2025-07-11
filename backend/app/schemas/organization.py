from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.common import OrganizationType

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: OrganizationType
    website: Optional[str] = None
    industry: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    owner_id: str

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[OrganizationType] = None
    website: Optional[str] = None
    industry: Optional[str] = None

class Organization(OrganizationBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 