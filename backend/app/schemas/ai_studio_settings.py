"""
AI Studio Settings Schemas
Pydantic models for AI Studio user settings
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AIStudioSettingsBase(BaseModel):
    """Base schema for AI Studio settings"""
    default_system_prompt: Optional[str] = Field(
        None,
        description="Custom system prompt override for content creation agent"
    )
    default_model: str = Field(
        default="openai/gpt-4o",
        description="Default OpenRouter model ID"
    )
    temperature: float = Field(
        default=0.70,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM responses"
    )


class AIStudioSettingsCreate(AIStudioSettingsBase):
    """Schema for creating AI Studio settings"""
    pass


class AIStudioSettingsUpdate(BaseModel):
    """Schema for updating AI Studio settings (all fields optional)"""
    default_system_prompt: Optional[str] = None
    default_model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class AIStudioSettings(AIStudioSettingsBase):
    """Schema for AI Studio settings response"""
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
