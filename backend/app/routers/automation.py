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
    """Active/désactive l'automation pour une conversation spécifique"""
    try:
        service = AutomationService(db)
        success = service.toggle_conversation_automation(
            conversation_id=conversation_id,
            user_id=current_user_id,
            enabled=request.enabled
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Impossible de modifier l'automation pour cette conversation"
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
    message_content: str = Query(..., description="Contenu du message à vérifier"),
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
) -> AutomationCheckResponse:
    """Vérifie si l'IA doit répondre automatiquement à un message"""
    try:
        service = AutomationService(db)
        result = service.should_auto_reply(
            conversation_id=conversation_id,
            message_content=message_content,
            user_id=current_user_id
        )
        
        return AutomationCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur vérification automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )