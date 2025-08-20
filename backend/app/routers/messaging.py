from fastapi import APIRouter, HTTPException, status
import logging
import re
from typing import List

from app.schemas.messaging import (
    UnifiedMessageRequest, BulkMessageRequest, BroadcastRequest,
    UnifiedMessageResponse, BulkMessageResponse, BroadcastResponse,
    Platform, MessageType, CapabilitiesResponse, SmartMessageRequest, SmartMessageResponse
)
from app.services.messaging_service import get_messaging_service

router = APIRouter(prefix="/messaging", tags=["Unified Messaging"])
logger = logging.getLogger(__name__)

@router.post("/send", response_model=UnifiedMessageResponse)
async def send_unified_message(request: UnifiedMessageRequest):
    """
    🚀 API unifiée pour envoyer des messages sur toutes les plateformes
    
    Supporte : WhatsApp, Instagram, Email, SMS, Push, Slack, Discord, Webhooks
    """
    try:
        service = await get_messaging_service()
        
        result = await service.send_message(
            platform=request.platform,
            message_type=request.message_type,
            recipient=request.recipient,
            content=request.content,
            # Paramètres WhatsApp
            access_token=request.access_token,
            phone_number_id=request.phone_number_id,
            template_name=request.template_name,
            language_code=request.language_code,
            media_type=request.media_type,
            media_url=request.media_url,
            # Paramètres Instagram
            page_id=request.page_id,
            caption=request.caption,
            image_url=request.image_url,
            # Paramètres Email
            subject=request.subject,
            is_html=request.is_html,
            # Paramètres Push/Slack/Discord
            title=request.title,
            channel=request.channel,
            username=request.username,
            # Paramètres additionnels
            **request.extra_params
        )
        
        return UnifiedMessageResponse(
            success=result.get("success", True),
            platform=request.platform.value,
            recipient=request.recipient,
            message_id=result.get("result", {}).get("messages", [{}])[0].get("id"),
            result=result,
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Erreur envoi unifié: {e}")
        return UnifiedMessageResponse(
            success=False,
            platform=request.platform.value,
            recipient=request.recipient,
            error=str(e)
        )

@router.post("/send-bulk", response_model=BulkMessageResponse)
async def send_bulk_messages(request: BulkMessageRequest):
    """
    📦 Envoyer plusieurs messages en lot sur différentes plateformes
    """
    try:
        service = await get_messaging_service()
        
        # Convertir les requêtes en format interne
        messages = []
        for msg in request.messages:
            message_data = {
                "platform": msg.platform.value,
                "message_type": msg.message_type.value,
                "recipient": msg.recipient,
                "content": msg.content,
                "extra_params": {
                    "access_token": msg.access_token,
                    "phone_number_id": msg.phone_number_id,
                    "page_id": msg.page_id,
                    "subject": msg.subject,
                    "title": msg.title,
                    "caption": msg.caption,
                    "template_name": msg.template_name,
                    "language_code": msg.language_code,
                    "media_type": msg.media_type,
                    "media_url": msg.media_url,
                    "image_url": msg.image_url,
                    "is_html": msg.is_html,
                    "channel": msg.channel,
                    "username": msg.username,
                    **msg.extra_params
                }
            }
            messages.append(message_data)
        
        result = await service.send_bulk_messages(messages)
        
        # Convertir les résultats en réponses structurées
        responses = []
        for res in result["results"]:
            responses.append(UnifiedMessageResponse(
                success=res.get("success", True),
                platform=res.get("platform", "unknown"),
                recipient=res.get("recipient", ""),
                result=res.get("result"),
                error=res.get("error")
            ))
        
        return BulkMessageResponse(
            total=result["total"],
            successful=result["successful"],
            failed=result["failed"],
            results=responses
        )
        
    except Exception as e:
        logger.error(f"Erreur bulk messaging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur bulk: {str(e)}"
        )

@router.post("/broadcast", response_model=BroadcastResponse)
async def broadcast_message(request: BroadcastRequest):
    """
    📡 Diffuser un message sur plusieurs plateformes simultanément
    """
    try:
        service = await get_messaging_service()
        
        result = await service.broadcast_message(
            platforms=request.platforms,
            message_type=request.message_type,
            recipients=request.recipients,
            content=request.content,
            subject=request.subject,
            title=request.title,
            **request.extra_params
        )
        
        # Calculer le résumé
        total_messages = sum(platform_data["total"] for platform_data in result.values())
        total_successful = sum(platform_data["successful"] for platform_data in result.values())
        total_failed = sum(platform_data["failed"] for platform_data in result.values())
        
        summary = {
            "total_messages": total_messages,
            "total_successful": total_successful,
            "total_failed": total_failed
        }
        
        return BroadcastResponse(
            platforms=result,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Erreur broadcast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur broadcast: {str(e)}"
        )

@router.post("/send-smart", response_model=SmartMessageResponse)
async def send_smart_message(request: SmartMessageRequest):
    """
    🧠 Envoi intelligent avec détection automatique de plateforme
    """
    try:
        service = await get_messaging_service()
        
        # Détection automatique de la plateforme
        detected_platform, confidence = detect_platform(request.recipient)
        
        if confidence < 0.7 and request.fallback_platforms:
            # Utiliser une plateforme de fallback
            detected_platform = request.fallback_platforms[0]
            fallback_used = True
        else:
            fallback_used = False
        
        # Envoyer le message
        result = await service.send_message(
            platform=detected_platform,
            message_type=request.message_type,
            recipient=request.recipient,
            content=request.content,
            subject=request.subject,
            title=request.title
        )
        
        return SmartMessageResponse(
            detected_platform=detected_platform,
            confidence=confidence,
            success=result.get("success", True),
            result=result,
            fallback_used=fallback_used,
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Erreur smart messaging: {e}")
        return SmartMessageResponse(
            detected_platform=Platform.EMAIL,  # fallback par défaut
            confidence=0.0,
            success=False,
            error=str(e)
        )

@router.get("/capabilities/{platform}", response_model=CapabilitiesResponse)
async def get_platform_capabilities(platform: Platform):
    """
    📋 Récupérer les capacités d'une plateforme spécifique
    """
    try:
        service = await get_messaging_service()
        capabilities = await service.get_platform_capabilities(platform)
        
        from app.schemas.messaging import PlatformCapabilities
        return CapabilitiesResponse(
            platform=platform,
            capabilities=PlatformCapabilities(**capabilities)
        )
        
    except Exception as e:
        logger.error(f"Erreur récupération capacités: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur capacités: {str(e)}"
        )

@router.get("/capabilities")
async def get_all_capabilities():
    """
    📋 Récupérer les capacités de toutes les plateformes
    """
    try:
        service = await get_messaging_service()
        
        all_capabilities = {}
        for platform in Platform:
            capabilities = await service.get_platform_capabilities(platform)
            all_capabilities[platform.value] = capabilities
        
        return {
            "platforms": all_capabilities,
            "supported_platforms": [p.value for p in Platform],
            "supported_message_types": [t.value for t in MessageType]
        }
        
    except Exception as e:
        logger.error(f"Erreur récupération toutes capacités: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )

@router.get("/health")
async def messaging_health_check():
    """
    ❤️ Vérifier la santé du service de messaging unifié
    """
    try:
        service = await get_messaging_service()
        
        platform_status = {}
        
        # Test basique pour chaque plateforme (sans envoi réel)
        for platform in Platform:
            try:
                capabilities = await service.get_platform_capabilities(platform)
                platform_status[platform.value] = {
                    "status": "available",
                    "message_types": capabilities.get("message_types", []),
                    "requires_credentials": capabilities.get("requires_credentials", True)
                }
            except Exception as e:
                platform_status[platform.value] = {
                    "status": "error",
                    "error": str(e)
                }
        
        overall_status = "healthy" if all(
            status["status"] == "available" for status in platform_status.values()
        ) else "partial"
        
        return {
            "service": "unified_messaging",
            "status": overall_status,
            "platforms": platform_status,
            "supported_platforms": len([p for p in platform_status.values() if p["status"] == "available"]),
            "total_platforms": len(Platform)
        }
        
    except Exception as e:
        logger.error(f"Erreur health check messaging: {e}")
        return {
            "service": "unified_messaging",
            "status": "unhealthy",
            "error": str(e)
        }

def detect_platform(recipient: str) -> tuple[Platform, float]:
    """
    Détecter automatiquement la plateforme basée sur le format du destinataire
    
    Returns:
        tuple: (Platform, confidence_score)
    """
    recipient = recipient.strip()
    
    # Email (contient @)
    if "@" in recipient and "." in recipient:
        return Platform.EMAIL, 0.95
    
    # Numéro de téléphone (chiffres uniquement, 8-15 caractères)
    if re.match(r'^\+?[0-9]{8,15}$', recipient.replace(" ", "").replace("-", "")):
        return Platform.WHATSAPP, 0.9  # WhatsApp par défaut pour les numéros
    
    # URL webhook (commence par http)
    if recipient.startswith(('http://', 'https://')):
        if 'slack.com' in recipient:
            return Platform.SLACK, 0.95
        elif 'discord.com' in recipient or 'discordapp.com' in recipient:
            return Platform.DISCORD, 0.95
        else:
            return Platform.WEBHOOK, 0.8
    
    # ID Instagram (format spécial)
    if recipient.isdigit() and len(recipient) > 10:
        return Platform.INSTAGRAM, 0.7
    
    # Par défaut : email
    return Platform.EMAIL, 0.3

@router.get("/detect-platform/{recipient}")
async def detect_recipient_platform(recipient: str):
    """
    🔍 Détecter automatiquement la plateforme pour un destinataire
    """
    platform, confidence = detect_platform(recipient)
    
    return {
        "recipient": recipient,
        "detected_platform": platform.value,
        "confidence": confidence,
        "suggestions": {
            "high_confidence": confidence >= 0.8,
            "recommended_action": "send" if confidence >= 0.7 else "confirm_platform",
            "alternative_platforms": [p.value for p in Platform if p != platform][:3]
        }
    }
