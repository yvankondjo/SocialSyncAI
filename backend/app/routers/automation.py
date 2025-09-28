from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
import logging

from app.core.security import get_current_user_id
from app.db.session import get_authenticated_db
from app.schemas.automation import (
    KeywordRuleCreate, KeywordRuleUpdate, KeywordRule, 
    AutomationToggleRequest, AutomationCheckResponse, KeywordRulesResponse
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
            user_id=current_user_id
        )
        
        return AutomationCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Erreur vérification automation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification: {str(e)}"
        )

@router.get("/keyword-rules", response_model=KeywordRulesResponse)
async def get_keyword_rules(
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Récupère toutes les règles de mots-clés de l'utilisateur"""
    try:
        service = AutomationService(db)
        rules = service.get_user_keyword_rules(current_user_id)
        
        return KeywordRulesResponse(
            rules=rules,
            total=len(rules)
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération règles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération: {str(e)}"
        )

@router.post("/keyword-rules", response_model=dict)
async def create_keyword_rule(
    rule: KeywordRuleCreate,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Crée une nouvelle règle de mots-clés"""
    try:
        service = AutomationService(db)
        rule_id = service.create_keyword_rule(
            user_id=current_user_id,
            scope_type=rule.scope_type,
            scope_id=rule.scope_id,
            keywords=rule.keywords,
            description=rule.description,
            match_type=rule.match_type
        )
        
        if not rule_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de créer la règle"
            )
        
        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Règle créée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur création règle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création: {str(e)}"
        )

@router.patch("/keyword-rules/{rule_id}")
async def update_keyword_rule(
    rule_id: str,
    updates: KeywordRuleUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Met à jour une règle de mots-clés"""
    try:
        # Vérifier que la règle appartient à l'utilisateur
        existing = db.table('automation_keyword_rules').select('*').eq(
            'id', rule_id
        ).eq('user_id', current_user_id).single().execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Règle non trouvée"
            )
        
        # Préparer les données de mise à jour
        update_data = {}
        if updates.keywords is not None:
            update_data['keywords'] = updates.keywords
        if updates.description is not None:
            update_data['description'] = updates.description
        if updates.is_enabled is not None:
            update_data['is_enabled'] = updates.is_enabled
        if updates.match_type is not None:
            update_data['match_type'] = updates.match_type
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucune donnée à mettre à jour"
            )
        
        # Effectuer la mise à jour
        db.table('automation_keyword_rules').update(
            update_data
        ).eq('id', rule_id).execute()
        
        return {
            "success": True,
            "message": "Règle mise à jour avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur mise à jour règle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.delete("/keyword-rules/{rule_id}")
async def delete_keyword_rule(
    rule_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Supprime une règle de mots-clés"""
    try:
        # Vérifier que la règle appartient à l'utilisateur et la supprimer
        result = db.table('automation_keyword_rules').delete().eq(
            'id', rule_id
        ).eq('user_id', current_user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Règle non trouvée"
            )
        
        return {
            "success": True,
            "message": "Règle supprimée avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression règle: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )
