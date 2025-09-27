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


class FAQQASearch(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = 10
    offset: int = 0


# Nouveaux schémas pour la gestion des questions
class FAQQuestionsAddRequest(BaseModel):
    items: List[str] = Field(..., min_items=1, description="Questions à ajouter")


class FAQQuestionsUpdateRequest(BaseModel):
    updates: List[Dict[str, Any]] = Field(..., description="Liste des mises à jour {index: int, value: str}")


class FAQQuestionsDeleteRequest(BaseModel):
    indexes: List[int] = Field(..., min_items=1, description="Indexes des questions à supprimer")


# Schémas pour les escalades
class SupportEscalation(BaseModel):
    id: UUID
    user_id: UUID
    conversation_id: UUID
    message_id: UUID
    confidence: float
    reason: Optional[str] = None
    notified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# Schémas pour le contrôle IA conversation
class ConversationAIModeRequest(BaseModel):
    mode: str = Field(..., description="Mode IA: ON ou OFF")

    class Config:
        schema_extra = {
            "example": {"mode": "OFF"}
        }
