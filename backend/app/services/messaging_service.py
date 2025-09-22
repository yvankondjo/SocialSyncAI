
import logging
from typing import Any, Dict, Optional, List, Union
from enum import Enum
from fastapi import HTTPException
from app.services.whatsapp_service import get_whatsapp_service
from app.services.instagram_service import get_instagram_service
from app.services.web_service import get_web_widget_service
logger = logging.getLogger(__name__)

class Platform(str, Enum):
    WHATSAPP = 'whatsapp'
    INSTAGRAM = 'instagram'
    WEB_CHAT = 'web_chat'

class MessageType(str, Enum):
    TEXT = 'text'
    MEDIA = 'media'
    TEMPLATE = 'template'
    POST = 'post'
    STORY = 'story'

class UnifiedMessagingService:
    """Service unifié pour l\'envoi de messages WhatsApp, Instagram et chat web intégrable"""

    def __init__(self):
        self.platform_services = {}

    async def send_message(self, platform: Platform, message_type: MessageType, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Méthode unifiée pour envoyer des messages sur WhatsApp, Instagram et le chat web
        
        Args:
            platform: Plateforme cible (whatsapp, instagram, web_chat)
            message_type: Type de message (text, media, template, post, story)
            recipient: Destinataire (numéro, ID, conversation_id)
            content: Contenu du message
            **kwargs: Arguments spécifiques à la plateforme
        """
        try:
            logger.info(f'Envoi {message_type} via {platform} vers {recipient}')
            
            if platform == Platform.WHATSAPP:
                return await self._send_whatsapp_message(message_type, recipient, content, **kwargs)
            elif platform == Platform.INSTAGRAM:
                return await self._send_instagram_message(message_type, recipient, content, **kwargs)
            elif platform == Platform.WEB_CHAT:
                return await self._send_web_chat_message(recipient, content, **kwargs)
            else:
                raise HTTPException(status_code=400, detail=f'Plateforme non supportée: {platform}')
                
        except Exception as e:
            logger.error(f'Erreur envoi {platform}: {e}')
            return {'success': False, 'platform': platform, 'error': str(e), 'recipient': recipient}

    async def send_bulk_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """\n        Envoyer plusieurs messages en lot sur différentes plateformes\n        \n        Args:\n            messages: Liste de messages avec platform, type, recipient, content\n        """  # inserted
        results = []
        successful = 0
        failed = 0
        for message in messages:
            try:
                result = await self.send_message(platform=Platform(message['platform']), message_type=MessageType(message['message_type']), recipient=message['recipient'], content=message['content'], **message.get('extra_params', {}))
            except Exception as e:
                    if result.get('success', True):
                        successful += 1
                    else:  # inserted
                        failed += 1
                    results.append(result)
        else:  # inserted
            return {'total': len(messages), 'successful': successful, 'failed': failed, 'results': results}
            failed += 1
            results.append({'success': False, 'platform': message.get('platform'), 'recipient': message.get('recipient'), 'error': str(e)})
            logger.error(f'Erreur message bulk: {e}')
            pass

    async def broadcast_message(self, platforms: List[Platform], message_type: MessageType, recipients: Dict[Platform, List[str]], content: str, **kwargs) -> Dict[str, Any]:
        """\n        Diffuser un message sur plusieurs plateformes simultanément\n        \n        Args:\n            platforms: Liste des plateformes cibles\n            message_type: Type de message\n            recipients: Mapping plateforme -> liste des destinataires\n            content: Contenu du message\n        """  # inserted
        results = {}
        for platform in platforms:
            platform_recipients = recipients.get(platform, [])
            if not platform_recipients:
                continue
            platform_results = []
            for recipient in platform_recipients:
                try:
                    result = await self.send_message(platform=platform, message_type=message_type, recipient=recipient, content=content, **kwargs)
                except Exception as e:
                        platform_results.append(result)
            else:  # inserted
                results[platform.value] = {'total': len(platform_recipients), 'successful': sum((1 for r in platform_results if r.get('success', True))), 'failed': sum((1 for r in platform_results if not r.get('success', True))), 'results': platform_results}
        else:  # inserted
            return results
            platform_results.append({'success': False, 'recipient': recipient, 'error': str(e)})

    async def _send_whatsapp_message(self, message_type: MessageType, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_whatsapp_service(kwargs.get('access_token'), kwargs.get('phone_number_id'))
        if message_type == MessageType.TEXT:
            result = await service.send_text_message(recipient, content, skip_validation=True)
            return {'success': True, 'platform': 'whatsapp', 'result': result}
        else:  # inserted
            if message_type == MessageType.TEMPLATE:
                template_name = kwargs.get('template_name', 'hello_world')
                language_code = kwargs.get('language_code', 'en_US')
                result = await service.send_template_message(recipient, template_name, language_code)
                return {'success': True, 'platform': 'whatsapp', 'result': result}
            else:  # inserted
                if message_type == MessageType.MEDIA:
                    media_type = kwargs.get('media_type', 'image')
                    media_url = kwargs.get('media_url') or content
                    caption = kwargs.get('caption', '')
                    result = await service.send_media_message(recipient, media_type, media_url, caption)
                    return {'success': True, 'platform': 'whatsapp', 'result': result}
                else:  # inserted
                    raise HTTPException(status_code=400, detail=f'Type de message WhatsApp non supporté: {message_type}')

    async def _send_instagram_message(self, message_type: MessageType, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        service = await get_instagram_service(kwargs.get('access_token'), kwargs.get('page_id'))
        if message_type == MessageType.TEXT:
            result = await service.send_direct_message(recipient, content)
            return {'success': True, 'platform': 'instagram', 'result': result}
        else:  # inserted
            if message_type == MessageType.POST:
                image_url = kwargs.get('image_url') or content
                caption = kwargs.get('caption', '')
                result = await service.publish_feed_post(image_url, caption)
                return {'success': True, 'platform': 'instagram', 'result': result}
            else:  # inserted
                if message_type == MessageType.STORY:
                    image_url = kwargs.get('image_url') or content
                    result = await service.publish_story(image_url)
                    return {'success': True, 'platform': 'instagram', 'result': result}
                else:  # inserted
                    raise HTTPException(status_code=400, detail=f'Type de message Instagram non supporté: {message_type}')

    async def _send_web_chat_message(self, recipient: str, content: str, **kwargs) -> Dict[str, Any]:
        """Envoyer un message via le chat web intégrable"""  # inserted
        service = await get_web_widget_service()
        widget_id = kwargs.get('widget_id')
        conversation_id = recipient
        user_info = kwargs.get('user_info', {})
        result = await service.process_chat_message(widget_id=widget_id, message=content, conversation_id=conversation_id, user_info=user_info)
        return {'success': True, 'platform': 'web_chat', 'result': result}

    async def get_platform_capabilities(self, platform: Platform) -> Dict[str, Any]:
        """Récupérer les capacités d\'une plateforme"""  # inserted
        capabilities = {Platform.WHATSAPP: {'message_types': ['text', 'media', 'template'], 'media_types': ['image', 'video', 'audio', 'document'], 'max_text_length': 4096, 'supports_markup': False, 'requires_credentials': True}, Platform.INSTAGRAM: {'message_types': ['text', 'post', 'story'], 'media_types': ['image', 'video'], 'max_text_length': 2200, 'supports_markup': False, 'requires_credentials': True}, Platform.WEB_CHAT: {'message_types': ['text'], 'media_types': [], 'max_text_length': 2000, 'supports_markup': True, 'requires_credentials': False, 'supports_ai_responses': True}}
        return capabilities.get(platform, {})
_messaging_service: Optional[UnifiedMessagingService] = None

async def get_messaging_service() -> UnifiedMessagingService:
    """Factory pour obtenir une instance du service unifié"""  # inserted
    global _messaging_service  # inserted
    if _messaging_service is None:
        _messaging_service = UnifiedMessagingService()
    return _messaging_service