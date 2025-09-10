from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

AIModelType = Literal[
    "anthropic/claude-3.5-haiku",
    "openai/gpt-4o",
    "openai/gpt-4o-mini", 
    "google/gemini-2.5-flash",
    "x-ai/grok-2"
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
    ai_model: AIModelType = "anthropic/claude-3.5-haiku"
    temperature: float = Field(default=0.20, ge=0.0, le=2.0)
    top_p: float = Field(default=1.00, ge=0.0, le=1.0)
    lang: LangType = "en"
    tone: ToneType = "friendly"
    is_active: bool = True

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

class AISettings(AISettingsBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AITestRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    settings: AISettingsBase

class AITestResponse(BaseModel):
    response: str
    response_time: float
    confidence: float
