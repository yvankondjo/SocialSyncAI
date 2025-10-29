from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging
import os

from app.db.session import get_authenticated_db
from app.schemas.escalation import SupportEscalation
from app.core.security import get_current_user_id
from app.services.escalation import Escalation
from app.services.link_service import LinkService

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
