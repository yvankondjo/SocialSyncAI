"""
Pydantic schemas for AI Decisions and Moderation
Handles AI decision logging, message checking, and escalations
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AIDecision(str, Enum):
    """AI decision types"""
    RESPOND = "respond"
    IGNORE = "ignore"
    ESCALATE = "escalate"


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
    should_respond: bool  # True if decision = "respond"
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
