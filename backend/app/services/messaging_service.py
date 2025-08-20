import logging
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from fastapi import HTTPException

from .whatsapp_service import get_whatsapp_service
from .instagram_service import get_instagram_service  
from .web_service import get_web_service

logger = logging.getLogger(__name__)

class Platform(str, Enum):
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"

class MessageType(str, Enum):
    TEXT = "text"
    MEDIA = "media"
    TEMPLATE = "template"
    POST = "post"
    STORY = "story"

class UnifiedMessagingService:
    """Service unifié pour l'envoi de messages sur toutes les plateformes"""
    
    def __init__(self):
        self.platform_services = {}
    
    async def send_message(self, 
                          platform: Platform,
                          message_type: MessageType,
                          recipient: str,
                          content: str,
                          **kwargs) -> Dict[str, Any]:
        """
        Méthode unifiée pour envoyer des messages sur toutes les plateformes
        
        Args:
            platform: Plateforme cible (whatsapp, instagram, email, etc.)
            message_type: Type de message (text, media, template, etc.)
            recipient: Destinataire (numéro, email, ID, etc.)
            content: Contenu du message
            **kwargs: Arguments spécifiques à la plateforme
        """
        try:
            logger.info(f"Envoi {message_type} via {platform} vers {recipient}")
            
            if platform == Platform.WHATSAPP:
                return await self._send_whatsapp_message(message_type, recipient, content, **kwargs)
            
            elif platform == Platform.INSTAGRAM:
                return await self._send_instagram_message(message_type, recipient, content, **kwargs)
            
            elif platform == Platform.EMAIL:
                return await self._send_email_message(recipient, content, **kwargs)
            
            elif platform == Platform.SMS:
                return await self._send_sms_message(recipient, content, **kwargs)
            
            elif platform == Platform.PUSH:
                return await self._send_push_notification(recipient, content, **kwargs)
            
            elif platform == Platform.SLACK:
                return await self._send_slack_message(recipient, content, **kwargs)
            
            elif platform == Platform.DISCORD:
                return await self._send_discord_message(recipient, content, **kwargs)
            
            elif platform == Platform.WEBHOOK:
                return await self._send_webhook_notification(recipient, content, **kwargs)
            
            else:
                raise HTTPException(status_code=400, detail=f"Plateforme non supportée: {platform}")
                
        except Exception as e:
            logger.error(f"Erreur envoi {platform}: {e}")
            return {
                "success": False,
                "platform": platform,
                "error": str(e),
                "recipient": recipient
            }

    async def send_bulk_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Envoyer plusieurs messages en lot sur différentes plateformes
        
        Args:
            messages: Liste de messages avec platform, type, recipient, content
        """
        results = []
        successful = 0
        failed = 0
        
        for message in messages:
            try:
                result = await self.send_message(
                    platform=Platform(message["platform"]),
                    message_type=MessageType(message["message_type"]),
                    recipient=message["recipient"],
                    content=message["content"],
                    **message.get("extra_params", {})
                )
                
                if result.get("success", True):
                    successful += 1
                else:
                    failed += 1
                    
                results.append(result)
                
            except Exception as e:
                failed += 1
                results.append({
                    "success": False,
                    "platform": message.get("platform"),
                    "recipient": message.get("recipient"),
                    "error": str(e)
                })
                logger.error(f"Erreur message bulk: {e}")
        
        return {
            "total": len(messages),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    async def broadcast_message(self, 
                               platforms: List[Platform],
                               message_type: MessageType,
                               recipients: Dict[Platform, List[str]],
                               content: str,
                               **kwargs) -> Dict[str, Any]:
        """
        Diffuser un message sur plusieurs plateformes simultanément
        
        Args:
            platforms: Liste des plateformes cibles
            message_type: Type de message
            recipients: Mapping plateforme -> liste des destinataires
            content: Contenu du message
        """
        results = {}
        
        for platform in platforms:
            platform_recipients = recipients.get(platform, [])
            if not platform_recipients:
                continue
                
            platform_results = []
            
            for recipient in platform_recipients:
                try:
                    result = await self.send_message(
                        platform=platform,
                        message_type=message_type,
                        recipient=recipient,
                        content=content,
                        **kwargs
                    )
                    platform_results.append(result)
                    
                except Exception as e:
                    platform_results.append({
                        "success": False,
                        "recipient": recipient,
                        "error": str(e)
                    })
            
            results[platform.value] = {
                "total": len(platform_recipients),
                "successful": sum(1 for r in platform_results if r.get("success", True)),
                "failed": sum(1 for r in platform_results if not r.get("success", True)),
                "results": platform_results
            }
        
        return results

    # Méthodes privées pour chaque plateforme
    async def _send_whatsapp_message(self, message_type: MessageType, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_whatsapp_service(kwargs.get("access_token"), kwargs.get("phone_number_id"))
        
        if message_type == MessageType.TEXT:
            result = await service.send_text_message(recipient, content, skip_validation=True)
            return {"success": True, "platform": "whatsapp", "result": result}
            
        elif message_type == MessageType.TEMPLATE:
            template_name = kwargs.get("template_name", "hello_world")
            language_code = kwargs.get("language_code", "en_US")
            result = await service.send_template_message(recipient, template_name, language_code)
            return {"success": True, "platform": "whatsapp", "result": result}
            
        elif message_type == MessageType.MEDIA:
            media_type = kwargs.get("media_type", "image")
            media_url = kwargs.get("media_url") or content  # content peut être l'URL
            caption = kwargs.get("caption", "")
            result = await service.send_media_message(recipient, media_type, media_url, caption)
            return {"success": True, "platform": "whatsapp", "result": result}
            
        else:
            raise HTTPException(status_code=400, detail=f"Type de message WhatsApp non supporté: {message_type}")

    async def _send_instagram_message(self, message_type: MessageType, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_instagram_service(kwargs.get("access_token"), kwargs.get("page_id"))
        
        if message_type == MessageType.TEXT:
            result = await service.send_direct_message(recipient, content)
            return {"success": True, "platform": "instagram", "result": result}
            
        elif message_type == MessageType.POST:
            image_url = kwargs.get("image_url") or content
            caption = kwargs.get("caption", "")
            result = await service.publish_feed_post(image_url, caption)
            return {"success": True, "platform": "instagram", "result": result}
            
        elif message_type == MessageType.STORY:
            image_url = kwargs.get("image_url") or content
            result = await service.publish_story(image_url)
            return {"success": True, "platform": "instagram", "result": result}
            
        else:
            raise HTTPException(status_code=400, detail=f"Type de message Instagram non supporté: {message_type}")

    async def _send_email_message(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        subject = kwargs.get("subject", "Notification SocialSync")
        is_html = kwargs.get("is_html", False)
        attachments = kwargs.get("attachments", [])
        
        result = await service.send_email(recipient, subject, content, is_html, attachments)
        return {"success": True, "platform": "email", "result": result}

    async def _send_sms_message(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        result = await service.send_sms_twilio(recipient, content)
        return {"success": True, "platform": "sms", "result": result}

    async def _send_push_notification(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        title = kwargs.get("title", "SocialSync")
        provider = kwargs.get("provider", "firebase")  # firebase ou onesignal
        
        if provider == "firebase":
            device_tokens = [recipient] if isinstance(recipient, str) else recipient
            result = await service.send_push_notification_firebase(device_tokens, title, content, kwargs.get("data"))
        else:  # onesignal
            player_ids = [recipient] if isinstance(recipient, str) else recipient
            result = await service.send_push_notification_onesignal(player_ids, title, content, kwargs.get("url"))
            
        return {"success": True, "platform": "push", "result": result}

    async def _send_slack_message(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        webhook_url = recipient  # Pour Slack, recipient est l'URL du webhook
        channel = kwargs.get("channel")
        username = kwargs.get("username", "SocialSync")
        
        result = await service.send_slack_message(webhook_url, content, channel, username)
        return {"success": True, "platform": "slack", "result": result}

    async def _send_discord_message(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        webhook_url = recipient  # Pour Discord, recipient est l'URL du webhook
        username = kwargs.get("username", "SocialSync")
        
        result = await service.send_discord_message(webhook_url, content, username)
        return {"success": True, "platform": "discord", "result": result}

    async def _send_webhook_notification(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_web_service()
        webhook_url = recipient
        payload = kwargs.get("payload", {"message": content})
        headers = kwargs.get("headers", {})
        
        result = await service.send_webhook_notification(webhook_url, payload, headers)
        return {"success": True, "platform": "webhook", "result": result}

    async def get_platform_capabilities(self, platform: Platform) -> Dict[str, Any]:
        """Récupérer les capacités d'une plateforme"""
        capabilities = {
            Platform.WHATSAPP: {
                "message_types": ["text", "media", "template"],
                "media_types": ["image", "video", "audio", "document"],
                "max_text_length": 4096,
                "supports_markup": False,
                "requires_credentials": True
            },
            Platform.INSTAGRAM: {
                "message_types": ["text", "post", "story"],
                "media_types": ["image", "video"],
                "max_text_length": 2200,
                "supports_markup": False,
                "requires_credentials": True
            },
            Platform.EMAIL: {
                "message_types": ["text"],
                "media_types": ["attachments"],
                "max_text_length": None,
                "supports_markup": True,
                "requires_credentials": True
            },
            Platform.SMS: {
                "message_types": ["text"],
                "media_types": [],
                "max_text_length": 160,
                "supports_markup": False,
                "requires_credentials": True
            },
            Platform.PUSH: {
                "message_types": ["text"],
                "media_types": [],
                "max_text_length": 256,
                "supports_markup": False,
                "requires_credentials": True
            },
            Platform.SLACK: {
                "message_types": ["text"],
                "media_types": ["attachments"],
                "max_text_length": 4000,
                "supports_markup": True,
                "requires_credentials": False
            },
            Platform.DISCORD: {
                "message_types": ["text"],
                "media_types": ["embeds"],
                "max_text_length": 2000,
                "supports_markup": True,
                "requires_credentials": False
            },
            Platform.WEBHOOK: {
                "message_types": ["text"],
                "media_types": [],
                "max_text_length": None,
                "supports_markup": True,
                "requires_credentials": False
            }
        }
        
        return capabilities.get(platform, {})

# Instance globale
_messaging_service: Optional[UnifiedMessagingService] = None

async def get_messaging_service() -> UnifiedMessagingService:
    """Factory pour obtenir une instance du service unifié"""
    global _messaging_service
    if _messaging_service is None:
        _messaging_service = UnifiedMessagingService()
    return _messaging_service
