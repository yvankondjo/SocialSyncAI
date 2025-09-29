from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging

from app.db.session import get_authenticated_db
from app.schemas.escalation import SupportEscalation
from app.core.security import get_current_user_id

router = APIRouter(prefix="/support", tags=["Support"])
logger = logging.getLogger(__name__)


@router.get("/escalations", response_model=List[SupportEscalation])
async def get_user_escalations(
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Récupère toutes les escalades de support de l'utilisateur"""
    try:
        result = db.table("support_escalations").select("*").eq("user_id", current_user_id).order("created_at", desc=True).execute()
        
        return [SupportEscalation(**item) for item in result.data]
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des escalades: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des escalades: {str(e)}"
        )


@router.post("/escalations/{escalation_id}/notify")
async def notify_escalation(
    escalation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Marque une escalade comme notifiée et envoie un email"""
    try:
        # Vérifier que l'escalade existe et appartient à l'utilisateur
        escalation = db.table("support_escalations").select("*").eq("id", escalation_id).eq("user_id", current_user_id).single().execute()
        
        if not escalation.data:
            raise HTTPException(status_code=404, detail="Escalade non trouvée")
        
        # Marquer comme notifiée
        result = db.table("support_escalations").update({
            "notified": True
        }).eq("id", escalation_id).execute()
        
        # TODO: Implémenter l'envoi d'email ici
        # await send_escalation_email(escalation.data)
        
        return {
            "message": "Notification envoyée avec succès",
            "escalation_id": escalation_id,
            "notified": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la notification: {str(e)}"
        )


@router.get("/escalations/{escalation_id}", response_model=SupportEscalation)
async def get_escalation(
    escalation_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Récupère une escalade spécifique"""
    try:
        result = db.table("support_escalations").select("*").eq("id", escalation_id).eq("user_id", current_user_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Escalade non trouvée")
        
        return SupportEscalation(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'escalade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'escalade: {str(e)}"
        )
