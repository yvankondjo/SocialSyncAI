import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
from app.services.automation_service import AutomationService
from app.services.message_timer_batcher import TimerBatch, message_timer_batcher
from app.services.instagram_service import InstagramService
from app.services.messenger_service import MessengerService
from app.services.whatsapp_service import WhatsAppService
from app.schemas.messages import (
    UnifiedMessageContent, MessageExtractionRequest, MessageSaveRequest,
    MessageSaveResponse, BatchMessageRequest, Platform, UnifiedMessageType
)
from langchain_core.messages import HumanMessage
from app.deps.system_prompt import SYSTEM_PROMPT
from app.services.token_utils import (
    count_tokens,
    is_message_too_long,
    get_max_input_tokens,
    get_model_context_window,
)

logger = logging.getLogger(__name__)



class RedisCache:
    _mem_cache: Dict[str, Any] = {}
    _breaker_until: Optional[float] = None
    _breaker_window_seconds = 300
    _breaker_trip_count = 0

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 3600) -> None:
        from app.core.redis_client import get_async_redis

        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.ttl_seconds = ttl_seconds
        self._client = None
        self._get_async_redis = get_async_redis
        self._memory_cache: Dict[str, Any] = {}
        self._memory_expirations: Dict[str, float] = {}
        self._use_memory_only = False

    @classmethod
    def _breaker_active(cls) -> bool:
        return bool(cls._breaker_until and time.time() < cls._breaker_until)

    @classmethod
    def _trip_breaker(cls, operation: str = "unknown", key: str = None) -> None:
        cls._breaker_until = time.time() + cls._breaker_window_seconds
        cls._breaker_trip_count += 1
        key_info = f" (key: {key[:50]}...)" if key else ""
        logger.warning(
            f"🔌 Redis breaker activé pour {cls._breaker_window_seconds}s après dépassement de quota "
            f"(opération: {operation}, total activations: {cls._breaker_trip_count}){key_info}"
        )

    async def _get_client(self):
        if self._use_memory_only:
            return None

        if not self._client:
            try:
                # Utiliser le helper qui gère SSL correctement
                self._client = self._get_async_redis()
            except Exception as exc:  # pragma: no cover - fallback resilience
                logger.warning("⚠️ Redis indisponible, bascule sur cache mémoire: %s", exc)
                self._use_memory_only = True
                self._client = None
        return self._client

    def _get_from_memory(self, key: str) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow().timestamp()
        expires_at = self._memory_expirations.get(key, 0)
        if expires_at and expires_at < now:
            self._memory_cache.pop(key, None)
            self._memory_expirations.pop(key, None)
            return None
        return self._memory_cache.get(key)

    def _set_in_memory(self, key: str, value: Dict[str, Any]) -> None:
        self._memory_cache[key] = value
        self._memory_expirations[key] = datetime.utcnow().timestamp() + self.ttl_seconds

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        if self._breaker_active():
            remaining = int(self._breaker_until - time.time()) if self._breaker_until else 0
            logger.debug(f"🔌 Redis breaker actif, utilisation cache mémoire (reste {remaining}s)")
            return self._get_from_memory(key)
        try:
            client = await self._get_client()
            if not client:
                return self._get_from_memory(key)
            raw = await client.get(key)
        except Exception as e:
            message = str(e).lower()
            if "max requests limit exceeded" in message:
                self._trip_breaker("get", key)
                return self._get_from_memory(key)
            logger.warning(f"⚠️ Redis get erreur: {e}")
            return self._get_from_memory(key)
        if raw is None:
            return self._get_from_memory(key)
        try:
            value = json.loads(raw)
            self._set_in_memory(key, value)
            return value
        except json.JSONDecodeError:
            logger.warning('Cache Redis invalide pour %s', key)
            return self._get_from_memory(key)

    async def set(self, key: str, value: Dict[str, Any]) -> None:
        if self._breaker_active():
            remaining = int(self._breaker_until - time.time()) if self._breaker_until else 0
            logger.debug(f"🔌 Redis breaker actif, utilisation cache mémoire (reste {remaining}s)")
            self._set_in_memory(key, value)
            return
        try:
            client = await self._get_client()
            if client:
                await client.set(key, json.dumps(value), ex=self.ttl_seconds)
            self._set_in_memory(key, value)
        except Exception as e:
            message = str(e).lower()
            if "max requests limit exceeded" in message:
                self._trip_breaker("set", key)
                self._set_in_memory(key, value)
                return
            logger.warning(f"⚠️ Redis set erreur: {e}")
            self._set_in_memory(key, value)

PROFILE_CACHE_TTL_SECONDS = 1800
profile_cache = RedisCache(ttl_seconds=PROFILE_CACHE_TTL_SECONDS)
credentials_cache = RedisCache(ttl_seconds=PROFILE_CACHE_TTL_SECONDS)
# conversation_cache removed - using in-memory batching instead



async def handle_messages_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:

    contacts_info = {}
    platform = user_info.get('platform', 'whatsapp')

    if platform == 'whatsapp':
        for contact in value.get('contacts', []):
            wa_id = contact.get('wa_id')
            if wa_id and 'profile' in contact:
                contacts_info[wa_id] = {
                    'name': contact['profile'].get('name'),
                    'wa_id': wa_id
                }
    elif platform == 'instagram':
        
        for message in value.get('messages', []):
            sender = message.get('sender', {})
            sender_id = sender.get('id')
            if sender_id:
               
                sender_username = sender.get('username') or sender.get('name')
                contacts_info[sender_id] = {
                    'name': sender_username or f'User_{sender_id[:8]}',
                    'id': sender_id
                }


    for message in value.get('messages', []):

        contact_id = message.get('from')
        if contact_id and contact_id in contacts_info:
            message['_contact_info'] = contacts_info[contact_id]

        await process_incoming_message_for_user(message, user_info)

    for status in value.get('statuses', []):
        await process_message_status_for_user(status, user_info)

async def send_error_notification_to_user(contact_id: str, message: str, platform: str, user_credentials: Dict[str, Any], message_id: str=None) -> str:
    await send_typing_indicator_and_mark_read(platform, user_credentials, contact_id, message_id)
    logger.info(f'📝 Typing indicator + read receipt sent for error message to {platform}:{contact_id}')
    await asyncio.sleep(5)
    result = await send_response(platform, user_credentials, contact_id, message)
    if not result:
        logger.error(f'Error sending notification to user {contact_id}: {message}')
        return
    return result

async def process_incoming_message_for_user(message: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    """
    process incoming message in a unified way for all platforms
    """
    platform = user_info.get('platform', 'whatsapp')
    account_id = user_info.get('account_id')
    message_id = message.get('id') or message.get('mid')
    contact_id = message.get('from')
    
    logger.info(
        f"Processing incoming {platform} message: id={message_id}, from={contact_id}, "
        f"user_id={user_info.get('user_id')}"
    )
 
    user_credentials = {
        'access_token': user_info.get('access_token'),
        'account_id': account_id
    }

    if not user_credentials['access_token']:
        logger.debug(f"Access token not in user_info, fetching from cache for {platform}:{account_id}")
        cached_credentials = await get_user_credentials_by_platform_account(platform, account_id)
        if not cached_credentials:
            logger.error('Unable to load credentials for %s:%s', platform, account_id)
            return None
        user_credentials['access_token'] = cached_credentials.get('access_token')
        user_credentials['account_id'] = cached_credentials.get('account_id')
        user_info.setdefault('social_account_id', cached_credentials.get('id'))
        user_info.setdefault('user_id', str(cached_credentials.get('user_id')))
    

    from app.schemas.messages import MessageExtractionRequest, Platform, UnifiedMessageContent, UnifiedMessageType
    platform_map = {
        'whatsapp': Platform.WHATSAPP,
        'instagram': Platform.INSTAGRAM,
        'messenger': Platform.MESSENGER,
    }
    platform_enum = platform_map.get(platform, Platform.WHATSAPP)

    feature_access = None
    user_subscription_id = str(user_info.get('user_id') or user_info.get('current_user_id'))
    if user_subscription_id and user_subscription_id != 'None':
        try:
            from app.services.credits_service import CreditsService
            from app.db.session import get_db
            credits_service = CreditsService(get_db())
            feature_access = await credits_service.get_feature_access(user_subscription_id)
        except Exception as e:
            logger.warning(f"Impossible de récupérer les fonctionnalités pour {user_subscription_id}: {e}")

    extracted_message: Optional[UnifiedMessageContent] = None
    message_type_hint = None

    if feature_access:
        if platform_enum == Platform.WHATSAPP:
            message_type_hint = message.get('type', 'text')
            if message_type_hint == 'image' and not feature_access.images:
                customer_name = None
                if '_contact_info' in message:
                    customer_name = message['_contact_info'].get('name')
                extracted_message = UnifiedMessageContent(
                    content='Media not supported for current plan',
                    token_count=0,
                    message_type=UnifiedMessageType.UNSUPPORTED,
                    message_id=message.get('id'),
                    message_from=message.get('from'),
                    platform=platform_enum,
                    customer_name=customer_name,
                    metadata={
                        'unsupported_type': 'image',
                        'reason': 'feature_not_allowed',
                        'required_feature': 'images'
                    }
                )
            elif message_type_hint in ('audio', 'voice', 'voice_message') and not feature_access.audio:
                customer_name = None
                if '_contact_info' in message:
                    customer_name = message['_contact_info'].get('name')
                extracted_message = UnifiedMessageContent(
                    content='Audio not supported for current plan',
                    token_count=0,
                    message_type=UnifiedMessageType.UNSUPPORTED,
                    message_id=message.get('id'),
                    message_from=message.get('from'),
                    platform=platform_enum,
                    customer_name=customer_name,
                    metadata={
                        'unsupported_type': 'audio',
                        'reason': 'feature_not_allowed',
                        'required_feature': 'audio'
                    }
                )
        else:  
            attachments = message.get('attachments', []) or []
            if attachments:
                attachment_type = attachments[0].get('type', '').lower()
                message_type_hint = attachment_type
                if attachment_type == 'image' and not feature_access.images:
                    extracted_message = UnifiedMessageContent(
                        content='Media not supported for current plan',
                        token_count=0,
                        message_type=UnifiedMessageType.UNSUPPORTED,
                        message_id=message.get('mid'),
                        message_from=message.get('from'),
                        platform=platform_enum,
                        metadata={
                            'unsupported_type': 'image',
                            'reason': 'feature_not_allowed',
                            'required_feature': 'images'
                        }
                    )
                elif attachment_type in ('audio', 'voice_media', 'voice_message') and not feature_access.audio:
                    extracted_message = UnifiedMessageContent(
                        content='Audio not supported for current plan',
                        token_count=0,
                        message_type=UnifiedMessageType.UNSUPPORTED,
                        message_id=message.get('mid'),
                        message_from=message.get('from'),
                        platform=platform_enum,
                        metadata={
                            'unsupported_type': 'audio',
                            'reason': 'feature_not_allowed',
                            'required_feature': 'audio'
                        }
                    )

    extraction_request = MessageExtractionRequest(
        platform=platform_enum,
        raw_message=message,
        user_credentials=user_credentials
    )

    if extracted_message is None:
        extracted_message = await extract_message_content_unified(extraction_request)

    if extracted_message is None:
        logger.error('Impossible to extract the incoming message for %s:%s', platform, contact_id)
        return None

    if contact_id == message_id:
        logger.info(f'Message is from the user itself, skipping extraction: {message}')
        try:
            save_request = MessageSaveRequest(
            platform=platform_enum,
            extracted_message=extracted_message,
            user_info=user_info,
            customer_name=extracted_message.customer_name
            )
            save_response = await save_unified_message(save_request)
            if not save_response.success or not save_response.conversation_message_id:
                logger.error('Message not saved in database')
                return None
            return save_response.conversation_message_id
        except Exception as e:
            logger.error(f'Error saving message to database: {e}')
            return None

    if extracted_message.message_type == UnifiedMessageType.UNSUPPORTED:
        unsupported_type = None
        if extracted_message.metadata:
            unsupported_type = extracted_message.metadata.get('unsupported_type')

        try:
            save_request = MessageSaveRequest(
                platform=platform_enum,
                extracted_message=extracted_message,
                user_info=user_info,
                customer_name=extracted_message.customer_name,
                customer_identifier=message.get('from')
            )
            save_response = await save_unified_message(save_request)
            if not save_response.success or not save_response.conversation_message_id:
                logger.error('Message non supporté non sauvegardé pour %s:%s', platform, contact_id)
        except Exception as e:
            logger.error(f'Error saving unsupported message to database: {e}')

        if unsupported_type:
            logger.warning('Message non supporté (%s) reçu depuis %s:%s', unsupported_type, platform, contact_id)
        else:
            logger.warning('Message non supporté reçu depuis %s:%s', platform, contact_id)

        if user_credentials and contact_id:
            error_text = 'This type of message is not supported yet.'
            if unsupported_type:
                error_text = f"The message of type {unsupported_type} is not supported yet."
            result = await send_error_notification_to_user(contact_id, error_text, platform, user_credentials, message_id)
            if not result:
                logger.error(f'Error sending notification to user {contact_id}: {error_text}')
        else:
            logger.error('Impossible to send notification for unsupported message: contact_id=%s, user_credentials=%s', contact_id, bool(user_credentials))
        return None
    
    # Obtenir le modèle depuis ai_settings ou utiliser un défaut
    ai_model = user_info.get('ai_settings', {}).get('ai_model', 'gpt-4o-mini') if user_info else 'gpt-4o-mini'
    
    # Compter les tokens du message avec tiktoken (via token_utils)
    message_text = extracted_message.text_content or ""
    message_tokens = count_tokens(message_text)
    
    # Vérifier si le message dépasse 90% du contexte du modèle
    if is_message_too_long(message_tokens, ai_model):
        max_tokens = get_max_input_tokens(ai_model)
        logger.error(f"Message too long: {message_tokens:,} tokens > {max_tokens:,} (90% of {ai_model} context)")
        try:
            save_request = MessageSaveRequest(
                platform=platform_enum,
                extracted_message=extracted_message,
                user_info=user_info,
                customer_name=extracted_message.customer_name
            )
            save_response = await save_unified_message(save_request)    
            if not save_response.success or not save_response.conversation_message_id:
                logger.error('Message not saved in database')
        except Exception as e:
            logger.error(f'Error saving message to database: {e}')
        try:
            result = await send_error_notification_to_user(contact_id, 'error your message is too long', platform, user_credentials, message_id)
            if not result:
                logger.error(f'Error sending notification to user {contact_id}: error your message is too long')
            return None
        except Exception as e:
            logger.error(f'Error detecting language: {e}')
            
    
    try:
        from app.schemas.messages import MessageSaveRequest
        save_request = MessageSaveRequest(
            platform=platform_enum,
            extracted_message=extracted_message,
            user_info=user_info,
            customer_name=extracted_message.customer_name,
            customer_identifier=message.get('from')
        )

        save_response = await save_unified_message(save_request)

        if not save_response.success or not save_response.conversation_message_id:
            logger.error('Message not saved in database')
            return None


        message_data = prepare_message_data_for_db(
            extracted_message,
            save_response.conversation_id,
            customer_identifier=contact_id
        )

        logger.debug(f"📋 Prepared message_data keys: {list(message_data.keys())}, has metadata: {'metadata' in message_data}, has conversation_id: {'conversation_id' in message_data}")
 
        from app.schemas.messages import BatchMessageRequest
        batch_request = BatchMessageRequest(
            platform=platform_enum,
            account_id=account_id,
            contact_id=contact_id,
            message_data=message_data,
            conversation_message_id=save_response.conversation_message_id
        )
        
        logger.info(f"📦 Preparing to add message {save_response.conversation_message_id} to batch for conversation {save_response.conversation_id} (platform={platform_enum.value}, account={account_id}, contact={contact_id})")
        success = await add_message_to_batch_unified(batch_request)

        if not success:
            logger.error(f'❌ Failed to add to batch for conversation {save_response.conversation_id}, message {save_response.conversation_message_id}')
            logger.warning('Message will remain in database - batch failure may be temporary (Redis issue)')
            # NE PAS supprimer le message - l'échec peut être temporaire (Redis down, etc.)
            # Le message reste en BDD et pourra être traité plus tard si nécessaire
            # delete_message_from_db(save_response.conversation_message_id)
            return None

        logger.info(
            "✅ Message %s successfully added to batch, will be processed within %ss",
            save_response.conversation_message_id,
            getattr(message_timer_batcher, "batch_window_seconds", 5),
        )
        return save_response.conversation_message_id
    except Exception as e:
        logger.error(f'Error saving message to DB: {e}')
        return None

async def process_message_status_for_user(status: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    message_id = status.get('id')
    status_type = status.get('status')
    logger.info(f"Status \'{status_type}\' for message {message_id} (user: {user_info['user_id']})")
    await update_message_status_in_user_db(message_id, status_type, user_info)

async def update_message_status_in_user_db(message_id: str, status: str, user_info: Dict[str, Any]) -> None:
    logger.info(f"Mise à jour statut {status} pour message {message_id} (utilisateur: {user_info['user_id']})")

async def handle_delivery_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    logger.info(f"Webhook de livraison pour l\'utilisateur {user_info['user_id']}")

async def handle_read_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    logger.info(f"Webhook de lecture pour l\'utilisateur {user_info['user_id']}")

async def process_webhook_change_for_user(change: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    field = change.get('field')
    value = change.get('value', {})
    logger.info(f"Traitement du changement \'{field}\' pour l\'utilisateur {user_info['user_id']}")
    if field == 'messages':
        await handle_messages_webhook_for_user(value, user_info)
    elif field == 'message_deliveries':
        await handle_delivery_webhook_for_user(value, user_info)
    elif field == 'message_reads':
        await handle_read_webhook_for_user(value, user_info)
    else:
        logger.info(f'Type de webhook non géré: {field}')

def delete_message_from_db(conversation_message_id: str) -> bool:
    """
    Supprime un message de la base de données en cas d'échec du batch

    Args:
        conversation_message_id: ID du message à supprimer

    Returns:
        bool: True si suppression réussie, False sinon
    """
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table('conversation_messages').delete().eq('id', conversation_message_id).execute()
        if res:
            logger.info(f'Message {conversation_message_id} supprimé suite à échec du batch')
            return True
        else:
            logger.error(f'Échec suppression message {conversation_message_id}')
            return False
    except Exception as e:
        logger.error(f'Erreur lors de la suppression du message {conversation_message_id}: {e}')
        return False



async def get_or_create_conversation(social_account_id: str, customer_identifier: str, customer_name: Optional[str]=None) -> Optional[str]:
    from app.db.session import get_db
    try:
        # No Redis caching - relying on in-memory message batching system
        db = get_db()
        res_find = db.table('conversations').select('id').eq('social_account_id', social_account_id).eq('customer_identifier', customer_identifier).order('created_at', desc=True).limit(1).execute()
        rows = res_find.data or []
        if rows:
            return str(rows[0]['id'])

        insert_payload = {
            'social_account_id': social_account_id,
            'customer_identifier': customer_identifier,
            'customer_name': customer_identifier if customer_name is None else customer_name,
            'status': 'open',
            'priority': 'normal'
        }
        res_create = db.table('conversations').insert(insert_payload).execute()
        if res_create and res_create.data:
            first = res_create.data[0]
            conversation_id = str(first.get('id')) if first and first.get('id') else None
            return conversation_id
        return None
    except Exception as e:
        logger.error(f'Erreur gestion conversation: {e}')
        return None



def encode_image_to_base64(image_content: bytes) -> str:
    import base64
    return base64.b64encode(image_content).decode('utf-8')


async def convert_image_url_to_base64(
    image_url: str,
    access_token: Optional[str] = None,
    timeout: float = 30.0
) -> Optional[str]:
    """
    Télécharge une image depuis une URL et la convertit en data URL base64.
    
    Les URLs d'images Instagram/Facebook/Messenger sont temporaires et signées,
    elles expirent rapidement. OpenAI ne peut pas y accéder directement.
    
    Cette fonction:
    1. Télécharge l'image côté serveur
    2. Détecte le type MIME
    3. Encode en base64
    4. Retourne une data URL utilisable par OpenAI Vision
    
    Args:
        image_url: URL de l'image à télécharger
        access_token: Token d'accès optionnel (pour Instagram/Facebook)
        timeout: Timeout de téléchargement en secondes
    
    Returns:
        Data URL base64 (ex: "data:image/jpeg;base64,/9j/4AAQ...") ou None si erreur
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "User-Agent": "SocialSyncAI/1.0",
                "Accept": "image/*",
            }
            
            # Ajouter le token d'autorisation si fourni
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            
            response = await client.get(image_url, headers=headers)
            
            # Retry avec token dans l'URL si 403
            if response.status_code == 403 and access_token:
                logger.warning(f"[IMAGE] 403 error, retrying with token in URL")
                signed_url = _append_access_token_to_url(image_url, access_token)
                headers_no_auth = {k: v for k, v in headers.items() if k != "Authorization"}
                response = await client.get(signed_url, headers=headers_no_auth)
            
            response.raise_for_status()
            image_bytes = response.content
        
        if not image_bytes:
            logger.warning(f"[IMAGE] Empty response from {image_url[:80]}...")
            return None
        
        # Détecter le type MIME
        mime_type = "image/jpeg"  # Par défaut
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            mime_type = "image/png"
        elif image_bytes[:3] == b'GIF':
            mime_type = "image/gif"
        elif image_bytes[:4] == b'RIFF' and len(image_bytes) > 12 and image_bytes[8:12] == b'WEBP':
            mime_type = "image/webp"
        
        # Encoder en base64
        base64_data = encode_image_to_base64(image_bytes)
        data_url = f"data:{mime_type};base64,{base64_data}"
        
        logger.info(f"[IMAGE] Converted to base64: {len(image_bytes)} bytes, {mime_type}")
        return data_url
        
    except httpx.HTTPStatusError as e:
        logger.error(f"[IMAGE] HTTP error downloading image: {e.response.status_code} - {image_url[:80]}...")
        return None
    except Exception as e:
        logger.error(f"[IMAGE] Error converting image to base64: {e}")
        return None


def resize_image(image_content: bytes, width: int, height: int) -> bytes:
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(image_content))
    
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    original_width, original_height = image.size
    
    if original_width <= width and original_height <= height:
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        logger.info(f'Image convertie en JPEG: {original_width}x{original_height} (pas de redimensionnement)')
        return output.getvalue()
    
    resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    resized_image.save(output, format='JPEG', quality=85, optimize=True)
    logger.info(f'Image redimensionnée et convertie en JPEG: {original_width}x{original_height} -> {width}x{height}')
    return output.getvalue()

def extract_image_dimensions(image_content: bytes) -> tuple[int, int]:
    """
    Extract the dimensions of an image from its binary content
    """
    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_content))
        width, height = image.size
        logger.debug(f'Dimensions extraites: {width}x{height}')
        return (width, height)
    except ImportError:
        logger.warning('PIL (Pillow) non disponible, utilisation des dimensions par défaut')
        return (None, None)
    except Exception as e:
        logger.warning(f'Erreur extraction dimensions: {e}')
        return (None, None)

def calculate_image_tokens(width: int=None, height: int=None) -> int:
    """
    Calculate approximately the tokens based on the size of the image
    """
    tokens_image = width * height / 750
    return tokens_image

def save_data_to_bucket(data: bytes, bucket_id: str, object_name: str, content_type: str = 'image/jpeg') -> str:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.storage.from_(bucket_id).upload(
            object_name, 
            data,
            file_options={"content-type": content_type}
        )
        logger.info(f'Upload vers bucket {bucket_id}: {res}')
        if res:
            return object_name
        logger.error(f'Erreur upload vers bucket {bucket_id}: {res}')
        return None
    except Exception as e:
        logger.error(f'Erreur lors de l\'upload vers Supabase Storage: {e}')
        return None

def get_signed_url(object_path: str, bucket_id: str='message', expires_in: int=3600) -> str:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.storage.from_(bucket_id).create_signed_url(object_path, expires_in)
        if res and ('signedURL' in res or 'signedUrl' in res):
            return res.get('signedURL') or res.get('signedUrl')
        logger.error(f'Erreur génération URL signée pour {object_path}: {res}')
        return None
    except Exception as e:
        logger.error(f'Erreur lors de la génération de l\'URL signée: {e}')
        return None


async def get_media_content(media_id: str, access_token: str) -> bytes:
    import os

    graph_version = os.getenv('META_GRAPH_VERSION', 'v24.0')

    client = httpx.AsyncClient()
    url = f'https://graph.facebook.com/{graph_version}/{media_id}'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    r1 = await client.get(url, headers=headers)
    r1.raise_for_status()
    media_url = r1.json().get('url')
    response = await client.get(media_url, headers=headers)
    response.raise_for_status()
    return response.content

def _append_access_token_to_url(url: str, token: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["access_token"] = token
    new_query = urlencode(query)
    return urlunparse(parsed._replace(query=new_query))


async def download_instagram_media(
    media_url: str,
    token: str,
    *,
    http_client: Optional[httpx.AsyncClient] = None,
) -> bytes:
    owns_client = http_client is None
    client = http_client or httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=10.0)
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "SocialSyncAI/1.0 (+https://socialsync.ai)",
        "Accept": "image/*",
        "Connection": "keep-alive",
    }

    try:
        response = await client.get(media_url, headers=headers)
        if response.status_code == 403:
            logger.warning(
                "Instagram media request returned 403. Retrying with signed URL."
            )
            signed_url = _append_access_token_to_url(media_url, token)
            fallback_headers = headers.copy()
            fallback_headers.pop("Authorization", None)
            response = await client.get(signed_url, headers=fallback_headers)
        response.raise_for_status()
        return response.content
    finally:
        if owns_client:
            await client.aclose()

async def generate_smart_response(messages: List[HumanMessage], user_id: str, ai_settings: Dict[str, Any], conversation_id: str) -> Optional[Dict[str, Any]]:
    import time
    start_time = time.time()
    logger.info(f"🧠 [GENERATE_RESPONSE] Starting generate_smart_response for user={user_id}, conversation={conversation_id}")
    logger.info(f"🧠 [GENERATE_RESPONSE] Messages count: {len(messages)}, AI settings: model={ai_settings.get('ai_model')}, doc_lang={ai_settings.get('doc_lang')}")
    
    from app.services.rag_agent import create_rag_agent
    from app.deps.credit_tracker import CreditTracker, get_or_create_credit_tracker
    from app.services.credits_service import CreditsService
    from app.db.session import get_db
    from app.deps.runtime_prod import get_checkpointer
    
    setup_start = time.time()

    logger.info(f"🧠 [GENERATE_RESPONSE] Creating RAG agent")

    db = get_db()
    request_cache: Dict[str, Any] = {}
    credits_service = CreditsService(db, request_cache=request_cache)
    credit_tracker = await get_or_create_credit_tracker(user_id, credits_service)
    logger.info(f"🧠 [GENERATE_RESPONSE] Credit tracker initialized (took {time.time() - setup_start:.2f}s)")

    agent_start = time.time()
    checkpointer = await get_checkpointer()
    agent = create_rag_agent(
        user_id=user_id,
        conversation_id=conversation_id,
        credit_tracker=credit_tracker,
        checkpointer=checkpointer,
        ai_settings=ai_settings
    )
    logger.info(f"🧠 [GENERATE_RESPONSE] RAG agent created with checkpointer (took {time.time() - agent_start:.2f}s)")
    
    try:
        feature_access = await credits_service.get_feature_access(user_id)
        logger.info(f"🧠 [GENERATE_RESPONSE] Feature access: {feature_access}")
        
        thread_id = f"1conversation:{conversation_id}day:{datetime.now().strftime('%Y-%m-%d')}"
        checkpoint_ns = f"user:{user_id}:conversation:{conversation_id}:{datetime.now().strftime('%Y-%m-%d')}"
        logger.info(f"🧠 [GENERATE_RESPONSE] Invoking agent with thread_id={thread_id}, checkpoint_ns={checkpoint_ns}")
        
        invoke_start = time.time()
        
        graph_config = {
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
                "checkpoint_ns": checkpoint_ns
            }
        }
        
        langsmith_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        if langsmith_tracing:
            logger.debug("✅ LangSmith tracing enabled - LangGraph will use env vars automatically")
        
        response = await agent.graph.ainvoke(
            {"messages": messages},
            config=graph_config
        )
        logger.info(f"🧠 [GENERATE_RESPONSE] Agent response received (took {time.time() - invoke_start:.2f}s), type={type(response)}")
        
        finalize_start = time.time()
        await credit_tracker.finalize_batch(conversation_id=conversation_id)
        logger.info(f"🧠 [GENERATE_RESPONSE] Credits finalized (took {time.time() - finalize_start:.2f}s): {credit_tracker.get_batch_info()}")
        
        total_time = time.time() - start_time
        logger.info(f"🧠 [GENERATE_RESPONSE] Total time: {total_time:.2f}s")
        logger.info(f"🧠 [GENERATE_RESPONSE] Response structure: {type(response)}, has 'messages': {hasattr(response, 'get') and response.get('messages') if isinstance(response, dict) else 'N/A'}")
        return response
    except Exception as e:
        logger.error(f"❌ [GENERATE_RESPONSE] Exception in generate_smart_response (took {time.time() - start_time:.2f}s): {e}", exc_info=True)
        try:
            await credit_tracker.finalize_batch(conversation_id=conversation_id)
        except Exception as finalize_error:
            logger.error(f"❌ [GENERATE_RESPONSE] Error finalizing batch after exception: {finalize_error}")
        return {"error": str(e)}


async def get_user_credentials_by_platform_account(platform: str, account_id: str) -> Optional[Dict[str, Any]]:
    logger.info(f"🔑 [GET_CREDENTIALS] Fetching credentials for {platform}:{account_id}")
    from app.db.session import get_db
    try:
        if platform not in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'whatsapp', 'messenger']:
            logger.error(f'❌ [GET_CREDENTIALS] Platform {platform} not supported')
            return None
        cache_key = f"credentials:{platform}:{account_id}"
        logger.info(f"🔍 [GET_CREDENTIALS] Checking cache for key: {cache_key}")
        cached = await credentials_cache.get(cache_key)
        if cached:
            logger.info(f"✅ [GET_CREDENTIALS] Credentials found in cache for {platform}:{account_id}")
            return cached

        logger.info(f"🔍 [GET_CREDENTIALS] Cache miss, querying database for {platform}:{account_id}")
        db = get_db()
        res = db.table('social_accounts').select('*').eq('platform', platform).eq('account_id', account_id).eq('is_active', True).limit(1).execute()
        rows = res.data or []
        if rows:
            record = rows[0]
            logger.info(f"✅ [GET_CREDENTIALS] Credentials found in DB for {platform}:{account_id}, user_id={record.get('user_id')}")
            await credentials_cache.set(cache_key, record)
            logger.info(f"💾 [GET_CREDENTIALS] Credentials cached for {platform}:{account_id}")
            return record
        logger.warning(f"⚠️ [GET_CREDENTIALS] No credentials found in DB for {platform}:{account_id}")
        return None
    except Exception as e:
        logger.error(f'❌ [GET_CREDENTIALS] Error retrieving credentials for {platform}:{account_id}: {e}', exc_info=True)
        return None

async def send_typing_indicator_and_mark_read(platform: str, user_credentials: Dict[str, Any], contact_id: str, message_id: str=None) -> bool:
    try:
        if platform == 'whatsapp':
            service = WhatsAppService(user_credentials.get('access_token'), user_credentials.get('account_id') or user_credentials.get('phone_number_id'))
            if message_id:
                result = await service.send_typing_and_mark_read(contact_id, message_id)
            else:
                logger.warning('Message ID requis pour WhatsApp typing indicator')
                return False
            return bool(result.get('messages'))
        elif platform == 'messenger':
            page_id = user_credentials.get('account_id') or user_credentials.get('page_id')
            if not page_id:
                logger.warning('page_id Messenger manquant - typing indicator ignoré')
                return False

            service = MessengerService(user_credentials.get('access_token'), page_id)
            result = await service.send_typing_and_mark_read(contact_id, message_id or '')
            if result.get('success'):
                logger.info(f"Messenger: Sender actions successful to {contact_id} - {result.get('message')}")
            else:
                logger.warning(f"❌ Failed sender actions Messenger to {contact_id}: {result.get('error')}")

            return result.get('success', False)
        elif platform == 'instagram':
            page_id = user_credentials.get('account_id') or user_credentials.get('instagram_business_account_id')
            if not page_id:
                logger.warning('account_id Instagram manquant dans user_credentials - typing indicator ignoré')
                return False

            service = InstagramService(user_credentials.get('access_token'), page_id)

            if message_id:
                result = await service.send_typing_and_mark_read(contact_id, message_id)

                if result.get('success'):
                    logger.info(f'Instagram: Sender actions successful to {contact_id} - {result.get("message")}')
                else:
                    logger.warning(f'❌ Failed sender actions Instagram to {contact_id}: {result.get("error")}')

                return result.get('success', False)
            else:
                logger.warning('Message ID requis pour Instagram sender actions')
                return False
        else:
            logger.error(f'Platform not supported for typing indicator: {platform}')
            return False
    except Exception as e:
        logger.error(f'Error sending typing indicator for {platform}: {e}')
        return False

async def send_response(platform: str, user_credentials: Dict[str, Any], contact_id: str, content: str) -> bool:
    logger.info(f"📤 [SEND_RESPONSE] Starting send_response for {platform}, contact_id={contact_id}, content_length={len(content) if content else 0}")
    try:
        if platform == 'whatsapp':
            logger.info(f"📤 [SEND_RESPONSE] Sending WhatsApp message to {contact_id}")
            service = WhatsAppService(user_credentials.get('access_token'), user_credentials.get('account_id') or user_credentials.get('phone_number_id'))
            result = await service.send_text_message(to=contact_id, text=content, skip_validation=True)
            success = bool(result.get('messages'))
            logger.info(f"{'✅' if success else '❌'} [SEND_RESPONSE] WhatsApp message {'sent' if success else 'failed'}: {result}")
            return success
        elif platform == 'messenger':
            logger.info(f"📤 [SEND_RESPONSE] Sending Messenger message to {contact_id}")
            page_id = user_credentials.get('account_id') or user_credentials.get('page_id')
            if not page_id:
                logger.error("page_id Messenger manquant - impossible d'envoyer la réponse Messenger")
                return False

            service = MessengerService(user_credentials.get('access_token'), page_id)
            result = await service.send_message(recipient_psid=contact_id, text=content)
            success = result.get('success', False)
            message_id = result.get('message_id') or result.get('result', {}).get('message_id')
            logger.info(f"{'✅' if success else '❌'} [SEND_RESPONSE] Messenger message {'sent' if success else 'failed'}: success={success}, message_id={message_id}, result={result}")
            return success
        elif platform == 'instagram':
            logger.info(f"📤 [SEND_RESPONSE] Sending Instagram DM to {contact_id}")
            page_id = user_credentials.get('account_id') or user_credentials.get('instagram_business_account_id')
            if not page_id:
                logger.error('account_id Instagram manquant dans user_credentials - impossible d\'envoyer la réponse Instagram')
                return False

            service = InstagramService(user_credentials.get('access_token'), page_id)
            logger.info(f"📤 [SEND_RESPONSE] InstagramService created, calling send_direct_message...")
            result = await service.send_direct_message(contact_id, content)
            success = result.get('success', False)
            message_id = result.get('message_id') or result.get('result', {}).get('id')
            logger.info(f"{'✅' if success else '❌'} [SEND_RESPONSE] Instagram DM {'sent' if success else 'failed'}: success={success}, message_id={message_id}, result={result}")
            return success
        else:
            logger.error(f"❌ [SEND_RESPONSE] Platform {platform} not supported")
            return False
    except Exception as e:
        logger.error(f'❌ [SEND_RESPONSE] Error sending response for {platform}: {e}', exc_info=True)
        return False

def save_response_to_db(
    conversation_id: str,
    content: str,
    user_id: str,
    confidence: Optional[float] = None
) -> Optional[str]:
    from app.db.session import get_db
    try:
        db = get_db()
        metadata_payload = {
            'content': content,
        }
        if confidence is not None:
            metadata_payload['confidence'] = confidence

        payload = {
            'conversation_id': conversation_id,
            'direction': 'outbound',
            'content': content,
            'message_type': 'text',
            'is_from_agent': False,
            'agent_id': user_id,
            'sender_id': 'user',
            'metadata': metadata_payload,
        }
        res = db.table('conversation_messages').insert(payload).execute()
        return res.data[0]['id'] if res.data else None
    except Exception as e:
        logger.error(f'Error saving response to database: {e}')





async def extract_message_content_unified(request: MessageExtractionRequest) -> Optional[UnifiedMessageContent]:
    """
    unified function to extract the content of WhatsApp and Instagram messages
    """
    try:
        if request.platform == Platform.WHATSAPP:
            return await extract_whatsapp_message_content(request.raw_message, request.user_credentials)
        elif request.platform == Platform.INSTAGRAM:
            return await extract_instagram_message_content(request.raw_message, request.user_credentials)
        elif request.platform == Platform.MESSENGER:
            return await extract_messenger_message_content(request.raw_message, request.user_credentials)
        else:
            logger.error(f"Platform not supported: {request.platform}")
            return None
    except Exception as e:
        logger.error(f"Error extracting unified content: {e}")
        return None

async def extract_whatsapp_message_content(message: Dict[str, Any], user_credentials: Dict[str, Any]) -> Optional[UnifiedMessageContent]:
    """
    extraction of the content for the WhatsApp messages
    """
    import tiktoken
    enc = tiktoken.get_encoding('o200k_harmony')

    if not message:
        return None

    customer_name = None
    if '_contact_info' in message:
        customer_name = message['_contact_info'].get('name')

    message_type = message.get('type', 'text')

    if message_type == 'text':
        content = message.get('text', {}).get('body', '')
        return UnifiedMessageContent(
            content=content,
            token_count=len(enc.encode(content)),
            message_type=UnifiedMessageType.TEXT,
            message_id=message.get('id'),
            message_from=message.get('from'),
            platform=Platform.WHATSAPP,
            customer_name=customer_name
        )

    elif message_type == 'image':
        import uuid
        caption = message.get('image', {}).get('caption', '')
        media_id = message.get('image', {}).get('id', '')
        message_id = message.get('id')

        try:
            media_content = await get_media_content(media_id, user_credentials.get('access_token'))
            width, height = extract_image_dimensions(media_content)

            if width > 768 or height > 768:
                media_content = resize_image(media_content, 768, 768)
                width, height = (768, 768)

            image_tokens = calculate_image_tokens(width, height)
            object_path = f"{uuid.uuid4()}/{message.get('id')}.jpg"
            saved_path = save_data_to_bucket(
                media_content, 
                bucket_id='message', 
                object_name=object_path,
                content_type='image/jpeg'
            )

            if not saved_path:
                logger.error('Error saving image WhatsApp in Supabase Storage')
                return None

            image_url = get_signed_url(saved_path, bucket_id='message', expires_in=3600*24)
            if not image_url:
                logger.error('Error generating signed URL for WhatsApp')
                return None

            if caption:
                text_tokens = len(enc.encode(f'[Image] {caption}'))
                content = [
                    {'type': 'text', 'text': caption},
                    {'type': 'image_url', 'image_url': {'url': image_url}}
                ]
                total_tokens = text_tokens + image_tokens
            else:
                content = [{'type': 'image_url', 'image_url': {'url': image_url}}]
                total_tokens = image_tokens

            total_tokens = int(total_tokens)

            return UnifiedMessageContent(
                content=content,
                token_count=total_tokens,
                message_type=UnifiedMessageType.IMAGE,
                message_id=message_id,
                message_from=message.get('from'),
                platform=Platform.WHATSAPP,
                customer_name=customer_name,
                storage_object_name=saved_path,
                media_type='image',
                caption=caption,
                media_url=image_url,
                media_id=media_id,
                metadata={
                    'width': width,
                    'height': height,
                    'file_size': len(media_content)
                }
            )
        except Exception as e:
            logger.error(f'Error downloading image WhatsApp: {e}')
            return None

    else:
        return UnifiedMessageContent(
                content='This Type of message is not supported yet',
                token_count=0,
                message_type=UnifiedMessageType.UNSUPPORTED,
                message_id=message.get('id'),
                message_from=message.get('from'),
                platform=Platform.WHATSAPP,
                customer_name=customer_name,
                storage_object_name=None,
                media_type=None,
                caption=None,
                media_url=None,
                media_id=None,
                metadata={
                    'width': None,
                    'height': None,
                    'file_size': None
                }
            )
        

async def extract_instagram_message_content(message: Dict[str, Any], user_credentials: Dict[str, Any]) -> Optional[UnifiedMessageContent]:
    """
    extraction of the content for the Instagram messages based on webhook structure
    """
    import tiktoken
    enc = tiktoken.get_encoding('o200k_harmony')

    if not message:
        return None
    message_type = 'text'  

    if 'text' in message:
        message_type = 'text'
    elif 'attachments' in message and message['attachments']:
        attachment = message['attachments'][0]
        message_type = attachment.get('type', 'unknown')
    else:
        logger.warning(f"Type of Instagram message not recognized: {message}")
        return None

    if message_type == 'text':
        content = message.get('text', '')
        return UnifiedMessageContent(
            content=content,
            token_count=len(enc.encode(content)),
            message_type=UnifiedMessageType.TEXT,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.INSTAGRAM,
            customer_name=None
        )

    elif message_type == 'image':
        import uuid
        attachments = message.get('attachments', [])
        if not attachments:
            logger.error('No attachments found for the Instagram image message')
            return None

        attachment = attachments[0]
        payload = attachment.get('payload', {})
        media_url = payload.get('url')

        if not media_url:
            logger.error('Media URL not found in the Instagram attachment')
            return None

        message_id = message.get('mid')

        token = (
            user_credentials.get("access_token")
            or user_credentials.get("page_access_token")
            or user_credentials.get("instagram_page_token")
            or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        )

        if not token:
            logger.error("Instagram image download aborted: missing access token")
            return None

        try:
            media_content = await download_instagram_media(media_url, token)

            width, height = extract_image_dimensions(media_content)

            if width and height and (width > 768 or height > 768):
                media_content = resize_image(media_content, 768, 768)
                width, height = (768, 768)

            image_tokens = calculate_image_tokens(width or 0, height or 0)
            object_path = f"{uuid.uuid4()}/{message_id}.jpg"
            saved_path = save_data_to_bucket(
                media_content,
                bucket_id='message',
                object_name=object_path,
                content_type='image/jpeg'
            )

            if not saved_path:
                logger.error('Error saving image Instagram in Supabase Storage')
                return None

            image_url = get_signed_url(saved_path, bucket_id='message', expires_in=3600*24)
            if not image_url:
                logger.error('Error generating signed URL for Instagram')
                return None

            content = [{'type': 'image_url', 'image_url': {'url': image_url}}]
            total_tokens = image_tokens

            total_tokens = int(total_tokens)

            return UnifiedMessageContent(
                content=content,
                token_count=total_tokens,
                message_type=UnifiedMessageType.IMAGE,
                message_id=message_id,
                message_from=message.get('from'),
                platform=Platform.INSTAGRAM,
                customer_name=None,
                storage_object_name=saved_path,
                media_type='image',
                media_url=image_url,
                metadata={
                    'width': width,
                    'height': height,
                    'file_size': len(media_content)
                }
            )
        except Exception as e:
            logger.error(f'Error downloading image Instagram: {e}')
            return None

    elif message_type == 'video':
        logger.warning('Message video Instagram received, not supported currently')
        return UnifiedMessageContent(
            content='Media not supported',
            token_count=0,
            message_type=UnifiedMessageType.UNSUPPORTED,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.INSTAGRAM,
            customer_name=None,
            metadata={'unsupported_type': 'video'}
        )
    elif message_type == 'audio':
        logger.warning('Message audio Instagram received, not supported currently')
        return UnifiedMessageContent(
            content='Media not supported',
            token_count=0,
            message_type=UnifiedMessageType.UNSUPPORTED,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.INSTAGRAM,
            customer_name=None,
            metadata={'unsupported_type': 'audio'}
        )
    elif message_type == 'story_mention':
        logger.warning('Story mention Instagram received, not supported currently')
        return UnifiedMessageContent(
            content='Story mention not supported',
            token_count=0,
            message_type=UnifiedMessageType.UNSUPPORTED,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.INSTAGRAM,
            customer_name=None,
            metadata={'unsupported_type': 'story_mention'}
        )
    else:
        logger.warning(f"Type of Instagram message not supported: {message_type}")
        return UnifiedMessageContent(
            content='This Type of message is not supported yet',
            token_count=0,
            message_type=UnifiedMessageType.UNSUPPORTED,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.INSTAGRAM,
            customer_name=None,
            metadata={'unsupported_type': message_type}
        )


async def extract_messenger_message_content(message: Dict[str, Any], user_credentials: Dict[str, Any]) -> Optional[UnifiedMessageContent]:
    """
    Extraction of the content for Messenger messages based on webhook structure
    """
    import tiktoken

    enc = tiktoken.get_encoding('o200k_harmony')

    if not message:
        return None

    customer_name = None
    if '_contact_info' in message:
        customer_name = message['_contact_info'].get('name')

    if 'text' in message and message.get('text'):
        content = message.get('text', '')
        return UnifiedMessageContent(
            content=content,
            token_count=len(enc.encode(content)),
            message_type=UnifiedMessageType.TEXT,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.MESSENGER,
            customer_name=customer_name,
        )

    attachments = message.get('attachments') or []
    if attachments:
        attachment = attachments[0]
        attachment_type = attachment.get('type', '').lower()
        payload = attachment.get('payload', {})
        media_url = payload.get('url')

        if attachment_type == 'image' and media_url:
            # Convertir l'image en base64 car les URLs Facebook/Messenger expirent
            access_token = user_credentials.get('access_token')
            base64_image = await convert_image_url_to_base64(media_url, access_token)
            
            if base64_image:
                content = [{'type': 'image_url', 'image_url': {'url': base64_image}}]
                tokens = len(enc.encode('[Image]')) + 100  # Estimation tokens pour base64
            else:
                # Fallback: utiliser l'URL directement (peut échouer si expirée)
                logger.warning(f"[MESSENGER] Failed to convert image to base64, using URL directly")
                content = [{'type': 'image_url', 'image_url': {'url': media_url}}]
                tokens = len(enc.encode('[Image]')) + len(enc.encode(media_url))
            
            return UnifiedMessageContent(
                content=content,
                token_count=int(tokens),
                message_type=UnifiedMessageType.IMAGE,
                message_id=message.get('mid'),
                message_from=message.get('from'),
                platform=Platform.MESSENGER,
                customer_name=customer_name,
                media_type='image',
                media_url=media_url,
                metadata={'unsupported_type': None}
            )

        logger.warning(f"Unsupported Messenger attachment type: {attachment_type}")
        return UnifiedMessageContent(
            content='Media not supported',
            token_count=0,
            message_type=UnifiedMessageType.UNSUPPORTED,
            message_id=message.get('mid'),
            message_from=message.get('from'),
            platform=Platform.MESSENGER,
            customer_name=customer_name,
            metadata={'unsupported_type': attachment_type or 'unknown'}
        )

    logger.warning(f"Messenger message structure not recognized: {message}")
    return UnifiedMessageContent(
        content='This Type of message is not supported yet',
        token_count=0,
        message_type=UnifiedMessageType.UNSUPPORTED,
        message_id=message.get('mid'),
        message_from=message.get('from'),
        platform=Platform.MESSENGER,
        customer_name=customer_name,
        metadata={'unsupported_type': 'unknown'}
    )

async def save_unified_message(request: MessageSaveRequest) -> MessageSaveResponse:
    """
    unified function to save an extracted message
    """
    try:

        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await get_or_create_conversation(
                social_account_id=request.user_info['social_account_id'],
                customer_identifier=request.extracted_message.message_from,
                customer_name=request.customer_name
            )

        if not conversation_id:
            return MessageSaveResponse(
                success=False,
                error=f"Unable to create/retrieve the conversation for {request.extracted_message.message_from}"
            )


        message_data = prepare_message_data_for_db(
            request.extracted_message,
            conversation_id,
            customer_identifier=request.customer_identifier or request.extracted_message.message_from
        )

        try:
            res = save_message_to_db(message_data)
            if res and res.data:
                conversation_message_id = str(res.data[0]['id'])
                response = MessageSaveResponse(
                    success=True,
                    conversation_message_id=conversation_message_id,
                    conversation_id=conversation_id
                )
                if request.platform == Platform.INSTAGRAM and request.extracted_message.message_from:
                    await update_instagram_conversation_profile(
                        user_info=request.user_info,
                        conversation_id=conversation_id,
                        instagram_user_id=request.extracted_message.message_from,
                        metadata=request.extracted_message.metadata or {},
                        fallback_name=request.customer_name,
                    )
                return response
            else:
                return MessageSaveResponse(
                    success=False,
                    error="Error saving to database"
                )
        except Exception as db_error:
            if 'unique_external_message_id' in str(db_error).lower():
                logger.info(f"Message {request.extracted_message.message_id} already processed")
                return MessageSaveResponse(
                    success=True,
                    conversation_message_id=None,
                    conversation_id=conversation_id
                )
            else:
                raise db_error

    except Exception as e:
        logger.error(f"Error saving unified message: {e}")
        return MessageSaveResponse(
            success=False,
            error=str(e)
        )

async def update_instagram_conversation_profile(
    user_info: Dict[str, Any],
    conversation_id: str,
    instagram_user_id: str,
    fallback_name: Optional[str],
    metadata: Dict[str, Any]
) -> None:
    access_token = user_info.get('access_token')
    if not access_token:
        return

    cache_key = f"instagram_profile:{instagram_user_id}"
    profile = await profile_cache.get(cache_key)
    if profile is None:
        profile = await fetch_instagram_user_profile(instagram_user_id, access_token)
        if profile:
            await profile_cache.set(cache_key, profile)
        else:
            profile = {}

    username = profile.get('username') or profile.get('name') or fallback_name or metadata.get('customer_name')
    avatar_url = profile.get('profile_pic') or metadata.get('customer_avatar_url')

    update_payload: Dict[str, Any] = {}
    if username:
        update_payload['customer_name'] = username
    if avatar_url:
        update_payload['customer_avatar_url'] = avatar_url

    if not update_payload:
        return

    from app.db.session import get_db
    db = get_db()
    try:
        db.table('conversations').update(update_payload).eq('id', conversation_id).execute()
    except Exception as exc:
        logger.error(f"Error updating Instagram profile for conversation {conversation_id}: {exc}")

async def fetch_instagram_user_profile(instagram_user_id: str, access_token: str) -> Optional[Dict[str, Any]]:
    url = f"https://graph.instagram.com/v23.0/{instagram_user_id}"
    params = {
        # Use correct fields for Instagram User Profile API (messaging)
        # profile_pic is the correct field for Instagram User IDs from messaging
        "fields": "name,username,profile_pic",
        "access_token": access_token
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)

            # If 400 error, log the response payload before retrying with alternate fields
            if response.status_code == 400:
                logger.warning(
                    "Instagram profile lookup returned 400 for %s (fields=%s): %s",
                    instagram_user_id,
                    params.get("fields"),
                    response.text,
                )
                params["fields"] = "name,username,profile_picture_url"
                response = await client.get(url, params=params, timeout=10.0)

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "Error retrieving Instagram profile %s (status=%s, fields=%s): %s",
                    instagram_user_id,
                    response.status_code,
                    params.get("fields"),
                    response.text,
                )
                raise exc

            profile = response.json()

            # Normalize field names: map profile_picture_url to profile_pic
            if 'profile_picture_url' in profile and 'profile_pic' not in profile:
                profile['profile_pic'] = profile['profile_picture_url']

            return profile
    except Exception as exc:
        logger.error(f"Error retrieving Instagram profile {instagram_user_id}: {exc}")
        return None

def prepare_message_data_for_db(
    extracted_message: UnifiedMessageContent,
    conversation_id: str,
    customer_identifier: Optional[str] = None
) -> Dict[str, Any]:
    """
    prepare message data for saving in the database
    """
    base_data = {
        'conversation_id': conversation_id,
        'external_message_id': extracted_message.message_id,
        'direction': 'inbound' if extracted_message.message_from != extracted_message.message_id else 'outbound',
        'message_type': extracted_message.message_type.value,
        'sender_id': customer_identifier or extracted_message.message_from,
        'status': 'received',
        'metadata': {
            'role': 'user',
            'platform': extracted_message.platform.value,
            **(extracted_message.metadata or {})
        }
    }


    if isinstance(extracted_message.content, str):
        base_data['content'] = extracted_message.content
        base_data['metadata']['content'] = extracted_message.content
    else:
        # Convert complex content (List[TextContent, ImageUrlContent]) to JSON-serializable format
        if isinstance(extracted_message.content, list):
            serializable_content = []
            for item in extracted_message.content:
                if hasattr(item, 'model_dump'):
                    serializable_content.append(item.model_dump())
                else:
                    serializable_content.append(str(item))
            base_data['content'] = serializable_content
            base_data['metadata']['content'] = serializable_content
        else:
            base_data['content'] = str(extracted_message.content)
            base_data['metadata']['content'] = str(extracted_message.content)


    if extracted_message.storage_object_name:
        base_data['storage_object_name'] = extracted_message.storage_object_name
        base_data['metadata']['storage_object_name'] = extracted_message.storage_object_name

    if extracted_message.media_type:
        base_data['media_type'] = extracted_message.media_type.value
        base_data['metadata']['media_type'] = extracted_message.media_type.value

    if extracted_message.caption:
        base_data['metadata']['caption'] = extracted_message.caption

    base_data['metadata']['token_count'] = extracted_message.token_count

    return base_data

def save_message_to_db(message_data: Dict[str, Any]) -> Any:
    """
    save a message in the database
    """
    from app.db.session import get_db
    db = get_db()
    return db.table('conversation_messages').insert(message_data).execute()


def _merge_timed_messages(batch: TimerBatch) -> HumanMessage:
    """Merge buffered messages while preserving image parts like the legacy batcher.

    Behaviour:
    - If any message is an image (or carries an image_url content part), we build a list of
      message parts mixing text blocks and image_url blocks so the downstream LLM can receive
      multimodal content.
    - If there are only text messages, we concatenate them with newlines (as before).
    """

    payloads: List[Dict[str, Any]] = []
    for msg in batch.messages:
        payload = msg.message_data or {}
        payloads.append(payload if isinstance(payload, dict) else {})

    def _has_image(payload: Dict[str, Any]) -> bool:
        if payload.get("message_type") == "image" or payload.get("media_type") == "image":
            return True
        content = payload.get("metadata", {}).get("content") or payload.get("content")
        if isinstance(content, list):
            return any(isinstance(part, dict) and part.get("type") == "image_url" for part in content)
        return False

    image_present = any(_has_image(p) for p in payloads)

    if image_present:
        merged_parts: List[Dict[str, Any]] = []

        def _append_text_part(value: str) -> None:
            cleaned = value.strip()
            if cleaned:
                merged_parts.append({"type": "text", "text": cleaned})

        for payload in payloads:
            content = payload.get("metadata", {}).get("content") or payload.get("content")
            message_type = payload.get("message_type") or payload.get("metadata", {}).get("message_type")

            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text" and part.get("text"):
                            _append_text_part(str(part.get("text")))
                        elif part.get("type") == "image_url" and part.get("image_url"):
                            merged_parts.append({"type": "image_url", "image_url": part.get("image_url")})
                    elif isinstance(part, str):
                        _append_text_part(part)
            elif isinstance(content, str):
                # If the message is typed as image but has a raw string, treat it as an image URL; otherwise text.
                if message_type == "image":
                    merged_parts.append({"type": "image_url", "image_url": {"url": content.strip()}})
                else:
                    _append_text_part(content)

        merged_content: Any = merged_parts if merged_parts else ""
    else:
        text_messages: List[str] = []

        def _append_text(value: str) -> None:
            cleaned = value.strip()
            if cleaned:
                text_messages.append(cleaned)

        for payload in payloads:
            content = payload.get("metadata", {}).get("content") or payload.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text" and part.get("text"):
                        _append_text(str(part.get("text")))
                    elif isinstance(part, str):
                        _append_text(part)
            elif isinstance(content, str):
                _append_text(content)

        merged_content = "\n".join(text_messages)

    return HumanMessage(content=merged_content)


async def _handle_timer_batch(batch: TimerBatch) -> bool:
    logger.info(
        "🚀 Processing in-memory batch for %s:%s:%s (messages=%s)",
        batch.platform,
        batch.account_id,
        batch.contact_id,
        len(batch.messages),
    )

    user_credentials = await get_user_credentials_by_platform_account(
        batch.platform, batch.account_id
    )
    if not user_credentials:
        logger.error(
            "❌ No credentials found for %s:%s — cannot respond",
            batch.platform,
            batch.account_id,
        )
        return False

    user_id = user_credentials.get("user_id")
    conversation_id = None
    if batch.messages:
        conversation_id = batch.messages[-1].message_data.get("conversation_id")

    automation_service = AutomationService()
    automation_check = automation_service.should_auto_reply(
        user_id=user_id,
        conversation_id=conversation_id,
        context_type="chat",
    )

    ai_settings = automation_check.get("ai_settings", {})
    ai_enabled_for_conversations = ai_settings.get("ai_enabled_for_conversations", True)

    if not ai_enabled_for_conversations or not automation_check.get("should_reply", True):
        logger.info(
            "🔕 Auto-response skipped for %s:%s:%s (reason=%s)",
            batch.platform,
            batch.account_id,
            batch.contact_id,
            automation_check.get("reason"),
        )
        return True

    external_message_id = None
    if batch.messages:
        external_message_id = batch.messages[-1].external_message_id

    human_messages = [_merge_timed_messages(batch)]
    response_result = await generate_smart_response(
        human_messages,
        user_id,
        ai_settings,
        conversation_id,
    )

    response_confidence = None
    if isinstance(response_result, dict) and "messages" in response_result:
        ai_message = None
        for msg in reversed(response_result["messages"]):
            if getattr(msg, "type", None) == "ai" or msg.__class__.__name__ == "AIMessage":
                ai_message = msg
                break
        if ai_message and hasattr(ai_message, "content"):
            raw_content = ai_message.content
            logger.debug(f"🔍 AI message raw_content type: {type(raw_content).__name__}, value: {raw_content!r}")
            # Handle case where content is already a dict
            if isinstance(raw_content, dict):
                response_content = raw_content.get("response", str(raw_content))
                response_confidence = raw_content.get("confidence")
            elif isinstance(raw_content, str):
                try:
                    content_data = json.loads(raw_content)
                    if isinstance(content_data, dict):
                        response_content = content_data.get("response", raw_content)
                        response_confidence = content_data.get("confidence")
                    else:
                        response_content = raw_content
                except (json.JSONDecodeError, KeyError, TypeError):
                    response_content = raw_content
            else:
                response_content = str(raw_content) if raw_content else None
        else:
            response_content = None
    elif isinstance(response_result, str):
        response_content = response_result
    else:
        response_content = None

    logger.info(f"📝 Extracted response_content: {response_content!r}, confidence: {response_confidence}")

    if not response_content:
        logger.error("❌ Response generation failed or returned empty content")
        return False

    if external_message_id:
        await send_typing_indicator_and_mark_read(
            batch.platform,
            user_credentials,
            batch.contact_id,
            external_message_id,
        )

    response_sent = await send_response(
        batch.platform,
        user_credentials,
        batch.contact_id,
        response_content,
    )

    if not response_sent:
        logger.error(
            "❌ Failed to send response for %s:%s:%s",
            batch.platform,
            batch.account_id,
            batch.contact_id,
        )
        return False

    message_assistant_group_id = save_response_to_db(
        conversation_id,
        response_content,
        user_id,
        confidence=response_confidence,
    )
    logger.info(
        "💾 Response saved to DB with group_id: %s for %s:%s:%s",
        message_assistant_group_id,
        batch.platform,
        batch.account_id,
        batch.contact_id,
    )
    return True


message_timer_batcher.set_handler(_handle_timer_batch)

async def add_message_to_batch_unified(request: BatchMessageRequest) -> bool:
    """Queue webhook messages for in-memory batching before replying."""

    logger.info(
        "🔄 Adding message to in-memory batch: platform=%s, account_id=%s, contact_id=%s, message_id=%s",
        request.platform.value,
        request.account_id,
        request.contact_id,
        request.conversation_message_id,
    )
    logger.debug(
        "Message data keys: %s",
        list(request.message_data.keys()) if request.message_data else "None",
    )

    try:
        success = await message_timer_batcher.add_message(
            platform=request.platform.value,
            account_id=request.account_id,
            contact_id=request.contact_id,
            message_data=request.message_data,
            conversation_message_id=request.conversation_message_id,
        )
        if success:
            logger.info(
                "✅ Message successfully added to in-memory batch for %s:%s:%s",
                request.platform.value,
                request.account_id,
                request.contact_id,
            )
        else:
            logger.error(
                "❌ Failed to add message to in-memory batch for %s:%s:%s",
                request.platform.value,
                request.account_id,
                request.contact_id,
            )
        return success
    except Exception as e:
        logger.error(
            "Error adding to in-memory batch: %s (message_id=%s)",
            e,
            request.conversation_message_id,
            exc_info=True,
        )
        return False

