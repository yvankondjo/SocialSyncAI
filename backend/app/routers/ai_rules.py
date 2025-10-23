"""
API Routes for AI Rules management
Simple AI control with instructions and ignore examples
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.schemas.ai_rules import (
    AIRulesCreate,
    AIRulesUpdate,
    AIRulesResponse,
    CheckMessageRequest,
    CheckMessageResponse,
    AIDecisionResponse,
    AIDecision,
)
from app.services.ai_decision_service import AIDecisionService
from app.db.session import get_authenticated_db

router = APIRouter(prefix="/ai-rules", tags=["AI Rules"])


@router.get("", response_model=Optional[AIRulesResponse])
async def get_ai_rules(db=Depends(get_authenticated_db)):
    """
    Get AI rules for current user
    Returns None if no rules exist yet
    """
    user_id = db.auth.get_user().user.id

    result = db.table("ai_rules").select("*").eq("user_id", user_id).execute()

    if not result.data:
        return None

    return AIRulesResponse(**result.data[0])


@router.post("", response_model=AIRulesResponse, status_code=201)
async def create_or_update_ai_rules(
    rules: AIRulesCreate,
    db=Depends(get_authenticated_db)
):
    """
    Create or update AI rules (UPSERT)
    If rules already exist for user, they will be updated
    """
    user_id = db.auth.get_user().user.id

    rules_data = rules.model_dump()
    rules_data["user_id"] = user_id
    rules_data["updated_at"] = datetime.utcnow().isoformat()

    # UPSERT: insert or update on conflict
    result = db.table("ai_rules").upsert(
        rules_data,
        on_conflict="user_id"
    ).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create/update AI rules")

    return AIRulesResponse(**result.data[0])


@router.patch("", response_model=AIRulesResponse)
async def update_ai_rules_partial(
    rules: AIRulesUpdate,
    db=Depends(get_authenticated_db)
):
    """
    Partial update of AI rules
    Only updates provided fields
    """
    user_id = db.auth.get_user().user.id

    # Check if rules exist
    existing = db.table("ai_rules").select("id").eq("user_id", user_id).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="AI rules not found. Create them first with POST /api/ai-rules")

    # Build update dict with only provided fields
    update_data = rules.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow().isoformat()

    result = db.table("ai_rules").update(update_data).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update AI rules")

    return AIRulesResponse(**result.data[0])


@router.patch("/toggle", response_model=AIRulesResponse)
async def toggle_ai_control(db=Depends(get_authenticated_db)):
    """
    Toggle AI control ON/OFF (master switch)
    Toggles ai_control_enabled between true and false
    """
    user_id = db.auth.get_user().user.id

    # Get current value
    existing = db.table("ai_rules").select("ai_control_enabled").eq("user_id", user_id).execute()

    if not existing.data:
        # Create default rules with AI disabled
        create_data = {
            "user_id": user_id,
            "ai_control_enabled": False,
            "ai_enabled_for_chats": True,
            "ai_enabled_for_comments": True,
            "ignore_examples": [],
        }
        result = db.table("ai_rules").insert(create_data).execute()
    else:
        # Toggle existing value
        current_value = existing.data[0]["ai_control_enabled"]
        result = db.table("ai_rules").update({
            "ai_control_enabled": not current_value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to toggle AI control")

    return AIRulesResponse(**result.data[0])


@router.post("/check-message", response_model=CheckMessageResponse)
async def check_message(
    request: CheckMessageRequest,
    context_type: str = "chat",
    db=Depends(get_authenticated_db)
):
    """
    Test if AI should respond to a message (dry-run)
    Does NOT log the decision to ai_decisions table

    Args:
        context_type: "chat" or "comment" for granular control
    """
    user_id = db.auth.get_user().user.id

    service = AIDecisionService(db, user_id)
    decision, confidence, reason, matched_rule = service.check_message(
        request.message_text,
        context_type=context_type
    )

    return CheckMessageResponse(
        decision=decision,
        confidence=confidence,
        reason=reason,
        should_respond=(decision == AIDecision.RESPOND),
        matched_rule=matched_rule if matched_rule else None
    )


@router.get("/decisions", response_model=List[AIDecisionResponse])
async def get_decisions_history(
    limit: int = 50,
    offset: int = 0,
    decision_filter: Optional[str] = None,
    db=Depends(get_authenticated_db)
):
    """
    Get history of AI decisions for current user

    Args:
        limit: Max number of results (default 50, max 100)
        offset: Pagination offset
        decision_filter: Filter by decision type (respond, ignore, escalate)
    """
    user_id = db.auth.get_user().user.id

    # Validate limit
    if limit > 100:
        limit = 100

    # Build query
    query = db.table("ai_decisions").select("*").eq("user_id", user_id)

    # Apply decision filter if provided
    if decision_filter:
        if decision_filter not in ["respond", "ignore", "escalate"]:
            raise HTTPException(status_code=400, detail="Invalid decision_filter. Must be: respond, ignore, or escalate")
        query = query.eq("decision", decision_filter)

    # Apply pagination and ordering
    result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    return [AIDecisionResponse(**item) for item in result.data]


@router.get("/decisions/stats")
async def get_decisions_stats(db=Depends(get_authenticated_db)):
    """
    Get statistics on AI decisions
    Returns count of RESPOND, IGNORE, ESCALATE decisions
    """
    user_id = db.auth.get_user().user.id

    # Count by decision type
    all_decisions = db.table("ai_decisions").select("decision").eq("user_id", user_id).execute()

    stats = {
        "respond": 0,
        "ignore": 0,
        "escalate": 0,
        "total": len(all_decisions.data)
    }

    for item in all_decisions.data:
        decision = item.get("decision")
        if decision in stats:
            stats[decision] += 1

    # Calculate percentages
    total = stats["total"]
    if total > 0:
        stats["respond_pct"] = round((stats["respond"] / total) * 100, 1)
        stats["ignore_pct"] = round((stats["ignore"] / total) * 100, 1)
        stats["escalate_pct"] = round((stats["escalate"] / total) * 100, 1)
    else:
        stats["respond_pct"] = 0.0
        stats["ignore_pct"] = 0.0
        stats["escalate_pct"] = 0.0

    return stats
