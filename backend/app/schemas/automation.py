from pydantic import BaseModel
from typing import List
from enum import Enum

class ScopeType(str, Enum):
    user = "user"
    account = "account" 
    conversation = "conversation"




class AutomationToggleRequest(BaseModel):
    enabled: bool

class AutomationCheckResponse(BaseModel):
    should_reply: bool
    reason: str
    matched_rules: List[str]

