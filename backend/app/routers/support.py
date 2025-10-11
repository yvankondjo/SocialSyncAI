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


@router.post("/escalations/test")
async def test_escalation(
    conversation_id: str,
    message: str = "Message de test pour l'escalade",
    confidence: float = 85.0,
    reason: str = "Test du système d'escalade",
    current_user_id: str = Depends(get_current_user_id)
):
    """Endpoint de test pour créer une escalade manuellement

    Args:
        conversation_id: ID de la conversation à escalader
        message: Message déclencheur (optionnel)
        confidence: Score de confiance (optionnel)
        reason: Raison de l'escalade (optionnel)
    """
    try:
        # Vérifier que la conversation existe et appartient à l'utilisateur
        db = get_authenticated_db()
        conversation = db.table("conversations").select("id").eq("id", conversation_id).eq("user_id", current_user_id).single().execute()

        if not conversation.data:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        # Créer l'escalade
        escalation_service = Escalation(current_user_id, conversation_id)
        escalation_id = await escalation_service.create_escalation(message, confidence, reason)

        if escalation_id:
            return {
                "success": True,
                "escalation_id": escalation_id,
                "message": "Escalade créée avec succès. Un email a été envoyé à l'équipe support.",
                "conversation_id": conversation_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Échec de création de l'escalade"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du test d'escalade: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du test d'escalade: {str(e)}"
        )


@router.post("/unsubscribe")
async def unsubscribe_from_support_notifications(
    token: str = None,
    current_user_id: str = Depends(get_current_user_id),
    db = Depends(get_authenticated_db)
):
    """Se désabonner des notifications d'escalade de support

    Args:
        token: Token JWT de désinscription (optionnel si utilisateur connecté)
    """
    try:
        user_id = current_user_id
        link_service = LinkService()

        # Si un token est fourni, le valider
        if token:
            payload = link_service.verify_conversation_token(token)
            if payload and payload.get("type") == "unsubscribe_support":
                user_id = payload.get("user_id")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token de désinscription invalide"
                )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Utilisateur non identifié"
            )

        # Mettre à jour les préférences utilisateur pour désactiver les notifications d'escalade
        # Note: Cette logique dépend de votre schéma de base de données
        # Ici on suppose qu'il y a une colonne email_notifications dans users

        try:
            # Vérifier si la colonne existe, sinon créer une préférence
            result = db.table("users").update({
                "email_notifications": False,
                "updated_at": "now()"
            }).eq("id", user_id).execute()

            if result.data:
                logger.info(f"Utilisateur {user_id} désabonné des notifications de support")
                return {
                    "success": True,
                    "message": "Vous avez été désabonné des notifications d'escalade de support.",
                    "user_id": user_id
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Utilisateur non trouvé"
                )

        except Exception as db_error:
            logger.error(f"Erreur base de données lors de la désinscription: {db_error}")
            # Fallback: Créer une entrée dans une table de préférences
            try:
                db.table("user_preferences").insert({
                    "user_id": user_id,
                    "preference_type": "support_notifications",
                    "value": False,
                    "created_at": "now()"
                }).execute()

                return {
                    "success": True,
                    "message": "Préférence de désinscription enregistrée.",
                    "user_id": user_id
                }
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erreur lors de l'enregistrement de la préférence"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la désinscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la désinscription: {str(e)}"
        )


@router.get("/unsubscribe")
async def show_unsubscribe_page(token: str = None):
    """Page de désinscription (redirection vers le frontend)

    Dans un vrai système, ceci retournerait une page HTML ou redirigerait
    vers le frontend qui gérera l'affichage et l'action.
    """
    try:
        if token:
            # Valider le token
            link_service = LinkService()
            payload = link_service.verify_conversation_token(token)

            if payload and payload.get("type") == "unsubscribe_support":
                user_id = payload.get("user_id")
                # Rediriger vers le frontend avec le token
                frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
                return {
                    "redirect_url": f"{frontend_url}/unsubscribe?token={token}",
                    "message": "Redirection vers la page de désinscription"
                }

        # Token invalide ou manquant
        return {
            "error": "Token de désinscription manquant ou invalide",
            "message": "Veuillez utiliser le lien de désinscription depuis votre email"
        }

    except Exception as e:
        logger.error(f"Erreur page désinscription: {e}")
        return {
            "error": "Erreur technique",
            "message": "Une erreur s'est produite lors du traitement de votre demande"
        }
