from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class SupportEscalation(BaseModel):
    id: UUID
    user_id: UUID
    conversation_id: UUID
    message: str
    confidence: float
    reason: Optional[str] = None
    notified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True