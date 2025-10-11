from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime

AIModelType = Literal[
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-pro"
]

ToneType = Literal[
    "friendly",
    "professional", 
    "casual",
    "neutral"
]

LangType = Literal[
    "en",
    "fr", 
    "es",
    "auto"
]

class AISettingsBase(BaseModel):
    system_prompt: str = Field(..., min_length=10, max_length=5000)
    ai_model: AIModelType = "openai/gpt-4o"
    temperature: float = Field(default=0.20, ge=0.0, le=2.0)
    top_p: float = Field(default=1.00, ge=0.0, le=1.0)
    lang: LangType = "en"
    tone: ToneType = "friendly"
    is_active: bool = True
    doc_lang: List[str] = Field(default_factory=list, description="Liste des langues des documents de l'utilisateur")

class AISettingsCreate(AISettingsBase):
    pass

class AISettingsUpdate(BaseModel):
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=5000)
    ai_model: Optional[AIModelType] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    lang: Optional[LangType] = None
    tone: Optional[ToneType] = None
    is_active: Optional[bool] = None
    doc_lang: Optional[List[str]] = Field(None, description="Liste des langues des documents de l'utilisateur")

class AISettings(AISettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AITestRequest(BaseModel):
    thread_id: str = Field(..., min_length=1, max_length=1000)
    message: str = Field(..., min_length=1, max_length=1000)
    settings: AISettingsBase

class AITestResponse(BaseModel):
    response: str
    response_time: float
    confidence: float
class AIResponse(BaseModel):
    """Json format for the response"""
    response: str
    confidence: float