from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class FAQQA(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    question: str
    answer: str
    tsconfig: str = "pg_catalog.simple"
    lang_code: str = "simple"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FAQQACreate(BaseModel):
    title: Optional[str] = None
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    lang_code: str = "simple"
    tsconfig: str = "pg_catalog.simple"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FAQQAUpdate(BaseModel):
    title: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    lang_code: Optional[str] = "simple"
    tsconfig: Optional[str] = "pg_catalog.simple"
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FAQQASearch(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = 10
    offset: int = 0
