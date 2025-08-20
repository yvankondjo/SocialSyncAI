from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import List
import logging
import hmac
import hashlib
import os

from app.schemas.whatsapp import (
    TextMessageRequest, TemplateMessageRequest, MediaMessageRequest,
    WhatsAppMessageResponse, WhatsAppCredentialsValidation, 
    BusinessProfileResponse, WhatsAppErrorResponse, SendMessageBatch, BatchResponse,
    WhatsAppCredentials, WebhookPayload, WebhookIncomingMessage, WebhookMessageStatus
)
from app.services.whatsapp_service import get_whatsapp_service, WhatsAppService

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
async def send_text_message(request: TextMessageRequest):
    """
    Envoyer un message texte WhatsApp
    
    Utilise les credentials de la requête ou ceux par défaut de l'environnement
    """
    try:
        service = await get_whatsapp_service(request.access_token, request.phone_number_id)
        
        result = await service.send_text_message(
            to=request.to,
            text=request.text,
            skip_validation=True  # Optimisation des performances
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
async def send_template_message(request: TemplateMessageRequest):
    """
    Envoyer un template WhatsApp approuvé
    
    Les templates sont plus fiables en mode développement
    """
    try:
        service = await get_whatsapp_service(request.access_token, request.phone_number_id)
        
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

@router.get("/health")
async def whatsapp_health_check():
    """
    Vérifier la santé du service WhatsApp
    """
    try:
        service = await get_whatsapp_service()
        validation = await service.validate_credentials()
        
        return {
            "service": "whatsapp",
            "status": "healthy" if validation["valid"] else "unhealthy",
            "details": validation
        }
        
    except Exception as e:
        logger.error(f"Erreur health check WhatsApp: {e}")
        return {
            "service": "whatsapp",
            "status": "unhealthy",
            "error": str(e)
        }

# Routes utilitaires
@router.get("/templates")
async def list_available_templates():
    """
    Lister les templates WhatsApp disponibles
    """
    return {
        "templates": [
            {
                "name": "hello_world",
                "language_codes": ["en_US", "fr_FR", "es_ES"],
                "description": "Template de base Meta pour tests"
            }
        ],
        "note": "En développement, seuls les templates approuvés par Meta sont disponibles"
    }

@router.get("/phone-formats")
async def get_phone_format_help():
    """
    Aide sur les formats de numéros de téléphone
    """
    return {
        "format": "Numéro international sans le +",
        "examples": {
            "france": "33612345678",
            "usa": "1234567890",
            "uk": "44712345678"
        },
        "rules": [
            "Pas de + au début",
            "Pas d'espaces ou de caractères spéciaux",
            "Entre 8 et 15 chiffres",
            "Inclure le code pays"
        ]
    }

# ==================== WEBHOOKS ====================

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Vérifier la signature du webhook WhatsApp
    """
    if not secret:
        logger.warning("WHATSAPP_WEBHOOK_SECRET non configuré - signature non vérifiée")
        return True  # En développement, on peut désactiver la vérification
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # WhatsApp envoie la signature au format "sha256=..."
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
        # Récupérer le payload et les headers
        payload = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")
        
        # Vérifier la signature (sécurité)
        webhook_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
        if not verify_webhook_signature(payload, signature, webhook_secret):
            logger.warning("Signature webhook invalide")
            raise HTTPException(status_code=403, detail="Signature invalide")
        
        # Parser le JSON
        webhook_data = await request.json()
        logger.info(f"Webhook reçu: {webhook_data}")
        
        # Traiter chaque entrée du webhook
        for entry in webhook_data.get("entry", []):
            await process_webhook_entry(entry)
        
        # Répondre rapidement à WhatsApp (obligatoire)
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook: {e}")
        # Toujours répondre 200 à WhatsApp pour éviter les retries
        return {"status": "error", "message": str(e)}

async def process_webhook_entry(entry: dict):
    """
    Traiter une entrée de webhook
    """
    entry_id = entry.get("id")
    changes = entry.get("changes", [])
    
    for change in changes:
        field = change.get("field")
        value = change.get("value", {})
        
        if field == "messages":
            # Messages entrants ou statuts de livraison
            await handle_messages_webhook(value)
        else:
            logger.info(f"Type de webhook non géré: {field}")

async def handle_messages_webhook(value: dict):
    """
    Gérer les webhooks de messages
    """
    # Messages entrants
    messages = value.get("messages", [])
    for message in messages:
        await process_incoming_message(message)
    
    # Statuts de livraison
    statuses = value.get("statuses", [])
    for status in statuses:
        await process_message_status(status)

async def process_incoming_message(message: dict):
    """
    Traiter un message entrant
    """
    message_id = message.get("id")
    from_number = message.get("from")
    timestamp = message.get("timestamp")
    message_type = message.get("type")
    
    logger.info(f"Message entrant de {from_number}: {message_type} (ID: {message_id})")
    
    # Traitement selon le type de message
    if message_type == "text":
        text_content = message.get("text", {}).get("body", "")
        logger.info(f"Contenu texte: {text_content}")
        
        # Ici vous pouvez ajouter votre logique métier :
        # - Sauvegarder en BDD
        # - Déclencher une réponse automatique
        # - Notifier un utilisateur
        await handle_incoming_text_message(from_number, text_content, message_id)
        
    elif message_type in ["image", "video", "audio", "document"]:
        media_info = message.get(message_type, {})
        logger.info(f"Média reçu: {media_info}")
        await handle_incoming_media_message(from_number, message_type, media_info, message_id)
    
    else:
        logger.info(f"Type de message non géré: {message_type}")

async def process_message_status(status: dict):
    """
    Traiter un statut de livraison
    """
    message_id = status.get("id")
    recipient_id = status.get("recipient_id")
    status_value = status.get("status")
    timestamp = status.get("timestamp")
    
    logger.info(f"Statut message {message_id}: {status_value} pour {recipient_id}")
    
    # Ici vous pouvez mettre à jour votre BDD avec le statut
    await update_message_status_in_db(message_id, status_value, timestamp)

# Fonctions de logique métier à implémenter selon vos besoins
async def handle_incoming_text_message(from_number: str, text: str, message_id: str):
    """
    Logique métier pour les messages texte entrants
    """
    # Exemple : réponse automatique simple
    if text.lower() in ["hello", "salut", "bonjour"]:
        try:
            service = await get_whatsapp_service()
            await service.send_text_message(
                to=from_number,
                text="Bonjour ! Merci pour votre message. Un agent vous répondra bientôt.",
                skip_validation=True
            )
            logger.info(f"Réponse automatique envoyée à {from_number}")
        except Exception as e:
            logger.error(f"Erreur réponse automatique: {e}")
    
    # TODO: Ajouter à votre logique de CRM/tickets
    logger.info(f"Message à traiter: {from_number} -> {text}")

async def handle_incoming_media_message(from_number: str, media_type: str, media_info: dict, message_id: str):
    """
    Logique métier pour les messages média entrants
    """
    media_id = media_info.get("id")
    caption = media_info.get("caption", "")
    
    logger.info(f"Média {media_type} reçu de {from_number}: ID={media_id}, Caption={caption}")
    
    # TODO: Télécharger et sauvegarder le média
    # TODO: Ajouter à votre système de tickets/CRM

async def update_message_status_in_db(message_id: str, status: str, timestamp: str):
    """
    Mettre à jour le statut d'un message dans votre BDD
    """
    # TODO: Implémenter selon votre schéma de BDD
    logger.info(f"À mettre à jour en BDD: Message {message_id} -> {status} à {timestamp}")

# ==================== ENDPOINTS WEBHOOK UTILITAIRES ====================

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

@router.post("/webhook-test")
async def test_webhook_locally(payload: dict):
    """
    Tester le traitement des webhooks en local
    """
    try:
        logger.info("Test webhook local")
        for entry in payload.get("entry", []):
            await process_webhook_entry(entry)
        return {"status": "success", "message": "Webhook testé avec succès"}
    except Exception as e:
        logger.error(f"Erreur test webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
