"""
Pydantic schemas for AI Rules feature
Simple AI control with instructions and ignore examples
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AIDecision(str, Enum):
    """AI decision types"""
    RESPOND = "respond"
    IGNORE = "ignore"
    ESCALATE = "escalate"


class AIRulesCreate(BaseModel):
    """Schema for creating AI rules"""
    instructions: Optional[str] = None
    ignore_examples: Optional[List[str]] = Field(default_factory=list)
    ai_control_enabled: bool = True
    ai_enabled_for_chats: bool = True
    ai_enabled_for_comments: bool = True
    flagged_keywords: Optional[List[str]] = Field(default_factory=list)
    flagged_phrases: Optional[List[str]] = Field(default_factory=list)


class AIRulesUpdate(BaseModel):
    """Schema for updating AI rules"""
    instructions: Optional[str] = None
    ignore_examples: Optional[List[str]] = None
    ai_control_enabled: Optional[bool] = None
    ai_enabled_for_chats: Optional[bool] = None
    ai_enabled_for_comments: Optional[bool] = None
    flagged_keywords: Optional[List[str]] = None
    flagged_phrases: Optional[List[str]] = None


class AIRulesResponse(BaseModel):
    """Schema for AI rules response"""
    id: str
    user_id: str
    instructions: Optional[str]
    ignore_examples: List[str]
    ai_control_enabled: bool
    ai_enabled_for_chats: bool
    ai_enabled_for_comments: bool
    flagged_keywords: List[str]
    flagged_phrases: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIDecisionCreate(BaseModel):
    """Schema for creating AI decision log"""
    message_id: Optional[str] = None
    decision: AIDecision
    confidence: float = Field(ge=0.0, le=1.0)
    reason: Optional[str] = None
    matched_rule: Optional[str] = None
    message_text: str
    snapshot_json: Optional[dict] = Field(default_factory=dict)


class AIDecisionResponse(BaseModel):
    """Schema for AI decision response"""
    id: str
    user_id: str
    message_id: Optional[str]
    decision: AIDecision
    confidence: float
    reason: Optional[str]
    matched_rule: Optional[str]
    message_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class CheckMessageRequest(BaseModel):
    """Request to check if AI should respond to a message"""
    message_text: str


class CheckMessageResponse(BaseModel):
    """Response from AI decision check"""
    decision: AIDecision
    confidence: float
    reason: str
    should_respond: bool  # True si decision = "respond"
    matched_rule: Optional[str] = None


# ============================================================================
# OpenAI Moderation Schemas
# ============================================================================

class OpenAIModerationResult(BaseModel):
    """Result from OpenAI Moderation API"""
    flagged: bool
    categories: Optional[dict] = None
    category_scores: Optional[dict] = None
    reason: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Email Escalation Schemas
# ============================================================================

class EscalationEmailCreate(BaseModel):
    """Request to create/send an escalation email"""
    email_to: str
    message_text: str
    reason: str
    context: dict = Field(default_factory=dict)


class EscalationEmailResponse(BaseModel):
    """Response from escalation_emails table"""
    id: str
    user_id: str
    message_id: Optional[str]
    decision_id: Optional[str]
    email_to: str
    email_subject: str
    email_body: str
    sent_at: datetime
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
