from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ScopeType(str, Enum):
    user = "user"
    account = "account" 
    conversation = "conversation"

class MatchType(str, Enum):
    contains = "contains"
    regex = "regex"

class KeywordRuleCreate(BaseModel):
    scope_type: ScopeType
    scope_id: Optional[str] = None
    keywords: List[str] = Field(..., min_items=1, description="Liste des mots-clés")
    description: Optional[str] = None
    match_type: MatchType = MatchType.contains

class KeywordRuleUpdate(BaseModel):
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    match_type: Optional[MatchType] = None

class KeywordRule(BaseModel):
    id: str
    user_id: str
    scope_type: ScopeType
    scope_id: Optional[str]
    keywords: List[str]
    description: Optional[str]
    match_type: MatchType
    is_enabled: bool
    created_at: str
    updated_at: str

class AutomationToggleRequest(BaseModel):
    enabled: bool

class AutomationCheckResponse(BaseModel):
    should_reply: bool
    reason: str
    matched_rules: List[str]

class KeywordRulesResponse(BaseModel):
    rules: List[KeywordRule]
    total: int
