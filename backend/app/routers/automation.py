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
    """Active/désactive l'automation pour une conversation spécifique (ai_mode)"""
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
                detail="Conversation non trouvée ou vous n'avez pas les permissions"
            )

        return {
            "success": True,
            "message": f"Automation {'activée' if request.enabled else 'désactivée'} pour cette conversation"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur toggle automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la modification: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/check")
async def check_automation_rules(
    conversation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
) -> AutomationCheckResponse:
    """Vérifie si l'IA doit répondre automatiquement à une conversation"""
    try:
        service = AutomationService()
        result = service.should_auto_reply(
            user_id=current_user_id,
            conversation_id=conversation_id,
            context_type="chat"
        )

        return AutomationCheckResponse(**result)

    except Exception as e:
        logger.error(f"Erreur vérification automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )