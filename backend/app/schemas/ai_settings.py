from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Literal, List, Union
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
    ai_model: str = Field(default="openai/gpt-4o", description="AI model identifier")
    temperature: float = Field(default=0.20, ge=0.0, le=2.0)
    top_p: float = Field(default=1.00, ge=0.0, le=1.0)
    lang: LangType = "en"
    tone: ToneType = "friendly"
    is_active: bool = True
    ai_enabled_for_conversations: bool = Field(default=True, description="Enable AI processing and auto-replies for DM/chat conversations")
    doc_lang: Optional[List[str]] = Field(default_factory=list, description="Liste des langues des documents de l'utilisateur")

    @field_validator('doc_lang', mode='before')
    @classmethod
    def parse_doc_lang(cls, v):
        if v is None:
            return []
        return v

    @field_validator('ai_model', mode='before')
    @classmethod
    def validate_ai_model(cls, v):
        # Liste des modèles valides
        valid_models = [
            "x-ai/grok-4", "x-ai/grok-4-fast",
            "openai/gpt-4o", "openai/gpt-4o-mini", "openai/gpt-5", "openai/gpt-5-mini",
            "anthropic/claude-3.5-sonnet", "anthropic/claude-sonnet-4", "anthropic/claude-sonnet-4.5",
            "anthropic/claude-3.5-haiku", "anthropic/claude-3-haiku",  # Anciens modèles
            "google/gemini-2.5-flash", "google/gemini-2.5-pro"
        ]

        # Si le modèle n'est pas dans la liste, utiliser le défaut
        if v not in valid_models:
            print(f"WARNING: Unknown ai_model '{v}', using default 'openai/gpt-4o'")
            return "openai/gpt-4o"
        return v

class AISettingsCreate(AISettingsBase):
    pass

class AISettingsUpdate(BaseModel):
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=5000)
    ai_model: Optional[str] = Field(None, description="AI model identifier")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    lang: Optional[LangType] = None
    tone: Optional[ToneType] = None
    is_active: Optional[bool] = None
    ai_enabled_for_conversations: Optional[bool] = Field(None, description="Enable AI processing and auto-replies for DM/chat conversations")
    doc_lang: Optional[List[str]] = Field(None, description="Liste des langues des documents de l'utilisateur")

class AISettings(AISettingsBase):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: str
    user_id: str
    created_at: Union[datetime, str]
    updated_at: Union[datetime, str]

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v

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