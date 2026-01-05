from fastapi import APIRouter, HTTPException, Depends, status, Query
import logging

from app.core.security import get_current_user_id
from app.db.session import get_authenticated_db
from app.schemas.automation import (
    AutomationToggleRequest, AutomationCheckResponse
)
from app.services.automation_service import AutomationService

router = APIRouter(prefix="/automation", tags=["Automation"])
logger = logging.getLogger(__name__)

@router.patch("/conversations/{conversation_id}/toggle")
async def toggle_conversation_automation(
    conversation_id: str,
    request: AutomationToggleRequest,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Enable/disable automation for a specific conversation (ai_mode)."""
    try:
        # Toggle ai_mode directly in conversations table
        target_mode = "ON" if request.enabled else "OFF"

        result = db.table("conversations") \
            .update({"ai_mode": target_mode}) \
            .eq("id", conversation_id) \
            .eq("user_id", current_user_id) \
            .execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conversation not found or you don't have permission"
            )

        return {
            "success": True,
            "message": f"Automation {'enabled' if request.enabled else 'disabled'} for this conversation"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while updating: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/check")
async def check_automation_rules(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
) -> AutomationCheckResponse:
    """Check whether the AI should auto-reply to a conversation."""
    try:
        service = AutomationService()
        result = service.should_auto_reply(
            user_id=current_user_id,
            conversation_id=conversation_id,
            context_type="chat"
        )

        return AutomationCheckResponse(**result)

    except Exception as e:
        logger.error(f"Error checking automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while checking: {str(e)}"
        )