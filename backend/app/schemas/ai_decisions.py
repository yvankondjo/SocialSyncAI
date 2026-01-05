"""
AI Decisions Schemas - Extracted from ai_rules for better separation of concerns
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class AIDecision(str, Enum):
    """Decision type for AI response"""

    ESCALATE = "escalate"  # Needs human review
    RESPOND = "respond"  # Auto-reply
    IGNORE = "ignore"  # Ignore message


class AIDecisionResponse(BaseModel):
    """Response schema for AI decisions"""

    id: str
    user_id: str
    message_id: Optional[str]
    message_text: str
    decision: AIDecision
    confidence: float
    reason: str
    matched_rule: Optional[str]
    created_at: datetime


class CheckMessageRequest(BaseModel):
    """Request schema for checking if AI should respond"""

    message_text: str
    context_type: str = "chat"  # "chat" or "comment"


class CheckMessageResponse(BaseModel):
    """Response schema for check_message endpoint"""

    should_respond: bool
    decision: AIDecision
    confidence: float
    reason: str
    matched_rule: Optional[str]


class AIDecisionStats(BaseModel):
    """Statistics about AI decisions"""

    total: int
    escalated: int
    responded: int
    ignored: int
    escalation_rate: float
    response_rate: float
