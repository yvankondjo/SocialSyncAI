from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List
import logging
import hmac
import hashlib
import os
from datetime import datetime, timezone
from app.core.security import get_current_user_id

from app.schemas.whatsapp import (
    TextMessageRequest, TemplateMessageRequest, MediaMessageRequest,
    WhatsAppMessageResponse, WhatsAppCredentialsValidation, 
    BusinessProfileResponse, SendMessageBatch, BatchResponse,
    WhatsAppCredentials
)
from app.services.whatsapp_service import get_whatsapp_service, WhatsAppService
from app.services.response_manager import (
    get_user_credentials_by_user_id,
    get_user_by_phone_number_id,
    process_webhook_change_for_user,
)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)

@router.post("/validate-credentials", response_model=WhatsAppCredentialsValidation)
async def validate_whatsapp_credentials(credentials: WhatsAppCredentials):
    """
    Valider les credentials WhatsApp Business API
    """
    try:
        async with WhatsAppService(credentials.access_token, credentials.phone_number_id) as service:
            validation_result = await service.validate_credentials()
            return WhatsAppCredentialsValidation(**validation_result)
    except Exception as e:
        logger.error(f"Erreur validation credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur validation: {str(e)}"
        )

@router.post("/send-text", response_model=WhatsAppMessageResponse)
async def send_text_message(
    request: TextMessageRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Envoyer un message texte WhatsApp
    
    Utilise les credentials de l'utilisateur connecté depuis la BDD
    """
    try:
        user_credentials = get_user_credentials_by_user_id(current_user_id)
        
        if not user_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun compte WhatsApp configuré pour cet utilisateur"
            )
        service = await get_whatsapp_service(
            user_credentials["access_token"], 
            user_credentials["phone_number_id"]
        )
        
        result = await service.send_text_message(
            to=request.to,
            text=request.text,
            skip_validation=True  
        )
        
        return WhatsAppMessageResponse(
            messaging_product=result["messaging_product"],
            contacts=result["contacts"],
            messages=result["messages"],
            message_type="text"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur envoi message texte: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur envoi message: {str(e)}"
        )

@router.post("/send-template", response_model=WhatsAppMessageResponse)
async def send_template_message(
    request: TemplateMessageRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Envoyer un template WhatsApp approuvé
    
    Utilise les credentials de l'utilisateur connecté
    """
    try:
        user_credentials = get_user_credentials_by_user_id(current_user_id)
        
        if not user_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun compte WhatsApp configuré pour cet utilisateur"
            )
        
        service = await get_whatsapp_service(
            user_credentials["access_token"], 
            user_credentials["phone_number_id"]
        )
        
        result = await service.send_template_message(
            to=request.to,
            template_name=request.template_name,
            language_code=request.language_code
        )
        
        return WhatsAppMessageResponse(
            messaging_product=result["messaging_product"],
            contacts=result["contacts"],
            messages=result["messages"],
            message_type="template"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur envoi template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur envoi template: {str(e)}"
        )

@router.post("/send-media", response_model=WhatsAppMessageResponse)
async def send_media_message(request: MediaMessageRequest):
    """
    Envoyer un message avec média (image, vidéo, audio, document)
    """
    try:
        service = await get_whatsapp_service(request.access_token, request.phone_number_id)
        
        result = await service.send_media_message(
            to=request.to,
            media_type=request.media_type.value,
            media_url=request.media_url,
            caption=request.caption
        )
        
        return WhatsAppMessageResponse(
            messaging_product=result["messaging_product"],
            contacts=result["contacts"],
            messages=result["messages"],
            message_type="media"
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur envoi média: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur envoi média: {str(e)}"
        )

@router.post("/send-batch", response_model=BatchResponse)
async def send_batch_messages(request: SendMessageBatch):
    """
    Envoyer plusieurs messages en lot (max 100)
    """
    try:
        service = await get_whatsapp_service(request.access_token, request.phone_number_id)
        
        results = []
        successful = 0
        failed = 0
        
        for message in request.messages:
            try:
                result = await service.send_text_message(
                    to=message.to,
                    text=message.text,
                    skip_validation=True
                )
                results.append({
                    "to": message.to,
                    "success": True,
                    "message_id": result["messages"][0]["id"],
                    "result": result
                })
                successful += 1
                
            except Exception as e:
                results.append({
                    "to": message.to,
                    "success": False,
                    "error": str(e)
                })
                failed += 1
                logger.error(f"Erreur envoi batch vers {message.to}: {e}")
        
        return BatchResponse(
            total_messages=len(request.messages),
            successful_messages=successful,
            failed_messages=failed,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Erreur envoi batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur envoi batch: {str(e)}"
        )

@router.get("/business-profile", response_model=BusinessProfileResponse)
async def get_business_profile(
    access_token: str = None, 
    phone_number_id: str = None
):
    """
    Récupérer le profil business WhatsApp
    """
    try:
        service = await get_whatsapp_service(access_token, phone_number_id)
        result = await service.get_business_profile()
        return BusinessProfileResponse(**result)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erreur récupération profil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur récupération profil: {str(e)}"
        )


# ==================== WEBHOOKS ====================

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Vérifier la signature du webhook WhatsApp
    """
    if not secret:
        logger.warning("WHATSAPP_WEBHOOK_SECRET non configuré - signature non vérifiée")
        return True  
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature.replace('sha256=', '') if signature.startswith('sha256=') else signature
    
    return hmac.compare_digest(expected_signature, received_signature)

@router.get("/webhook")
async def webhook_verification(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"), 
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """
    Vérification du webhook WhatsApp (étape d'activation)
    
    Meta envoie une requête GET pour vérifier que votre endpoint est valide
    """
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
    
    if not verify_token:
        logger.error("WHATSAPP_VERIFY_TOKEN non configuré")
        raise HTTPException(status_code=500, detail="Token de vérification non configuré")
    
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook WhatsApp vérifié avec succès")
        return PlainTextResponse(content=hub_challenge)
    
    logger.warning(f"Échec vérification webhook: mode={hub_mode}, token_match={hub_verify_token == verify_token}")
    raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    Gestionnaire principal des webhooks WhatsApp
    
    Reçoit :
    - Messages entrants des utilisateurs
    - Statuts de livraison des messages envoyés
    - Événements de lecture/écriture
    """
    try:
        
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")

        webhook_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
        if not verify_webhook_signature(payload, signature, webhook_secret):
            logger.warning("Signature webhook invalide")
            raise HTTPException(status_code=403, detail="Signature invalide")
        
        webhook_data = await request.json()
        logger.info(f"Webhook reçu: {webhook_data}")
        
        for entry in webhook_data.get("entry", []):
            print(f"entry: {entry} message: {webhook_data.get('message')}")
            await process_webhook_entry_with_user_routing(entry)
        
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/webhook-test")
async def test_webhook_locally(payload: dict):
    """
    Tester le traitement des webhooks en local
    """
    try:
        logger.info("Test webhook local")
        for entry in payload.get("entry", []):
            await process_webhook_entry_with_user_routing(entry)
        return {"status": "success", "message": "Webhook testé avec succès"}
    except Exception as e:
        logger.error(f"Erreur test webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_webhook_entry_with_user_routing(entry: dict):
    """Traiter une entrée de webhook WhatsApp avec routage utilisateur"""
    phone_number_id = entry.get("changes")[0].get("value").get("metadata").get("phone_number_id") 
    changes = entry.get("changes", [])
    
    user_info = get_user_by_phone_number_id(phone_number_id)
    
    if not user_info:
        logger.warning(f"Aucun utilisateur trouvé pour phone_number_id: {phone_number_id}")
        return
    
    logger.info(f"Webhook routé vers l'utilisateur {user_info['user_id']} (phone: {phone_number_id})")
    
    
    for change in changes:
        await process_webhook_change_for_user(change, user_info)

@router.get("/webhook-info")
async def get_webhook_info():
    """
    Informations sur la configuration des webhooks
    """
    return {
        "webhook_url": "/api/whatsapp/webhook",
        "verification_url": "/api/whatsapp/webhook?hub.mode=subscribe&hub.challenge=CHALLENGE&hub.verify_token=TOKEN",
        "required_env_vars": [
            "WHATSAPP_VERIFY_TOKEN - pour la vérification initiale",
            "WHATSAPP_WEBHOOK_SECRET - pour vérifier les signatures (optionnel en dev)"
        ],
        "webhook_events": [
            "messages - messages entrants et statuts de livraison",
            "message_deliveries - accusés de réception", 
            "message_reads - accusés de lecture"
        ],
        "setup_steps": [
            "1. Configurer WHATSAPP_VERIFY_TOKEN dans .env",
            "2. Configurer l'URL webhook dans Meta for Developers",
            "3. Activer les événements souhaités",
            "4. Tester avec l'endpoint de vérification"
        ]
    }