from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class FAQQA(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    questions: List[str] = Field(default_factory=list)
    answer: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FAQQACreate(BaseModel):
    title: Optional[str] = None
    questions: List[str] = Field(..., min_items=1, description="Liste des formulations de questions")
    answer: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FAQQAUpdate(BaseModel):
    title: Optional[str] = None
    questions: Optional[List[str]] = None
    answer: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class FAQQuestionsAddRequest(BaseModel):
    items: List[str] = Field(..., min_items=1, description="Questions à ajouter")


class FAQQuestionsUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., description="Liste des mises à jour {index: int, value: str}")


class FAQQuestionsDeleteRequest(BaseModel):
    indexes: List[int] = Field(..., min_items=1, description="Indexes des questions à supprimer")






