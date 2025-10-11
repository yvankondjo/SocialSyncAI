import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional, List
from app.services.message_batcher import MessageBatcher
from app.services.instagram_service import InstagramService
from app.services.whatsapp_service import WhatsAppService
from app.schemas.messages import (
    UnifiedMessageContent, MessageExtractionRequest, MessageSaveRequest,
    MessageSaveResponse, BatchMessageRequest, Platform, UnifiedMessageType
)
from langchain_core.messages import HumanMessage
from app.deps.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)
message_batcher = MessageBatcher()



class RedisCache:
    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 3600) -> None:
        import redis.asyncio as redis_async

        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.ttl_seconds = ttl_seconds
        self._pool: Optional[redis_async.ConnectionPool] = None
        self._redis_module = redis_async

    async def _get_client(self):
        if not self._pool:
            self._pool = self._redis_module.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20
            )
        return self._redis_module.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        client = await self._get_client()
        raw = await client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning('Cache Redis invalide pour %s', key)
            return None

    async def set(self, key: str, value: Dict[str, Any]) -> None:
        client = await self._get_client()
        await client.set(key, json.dumps(value), ex=self.ttl_seconds)

PROFILE_CACHE_TTL_SECONDS = 3600
profile_cache = RedisCache(ttl_seconds=PROFILE_CACHE_TTL_SECONDS)
credentials_cache = RedisCache(ttl_seconds=PROFILE_CACHE_TTL_SECONDS)
conversation_cache = RedisCache(ttl_seconds=PROFILE_CACHE_TTL_SECONDS)



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
    import time
    time.sleep(5)
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
 
    user_credentials = {
        'access_token': user_info.get('access_token'),
        'account_id': account_id
    }

    if not user_credentials['access_token']:
        cached_credentials = await get_user_credentials_by_platform_account(platform, account_id)
        if not cached_credentials:
            logger.error('Unable to load credentials for %s:%s', platform, account_id)
            return None
        user_credentials['access_token'] = cached_credentials.get('access_token')
        user_credentials['account_id'] = cached_credentials.get('account_id')
        user_info.setdefault('social_account_id', cached_credentials.get('id'))
        user_info.setdefault('user_id', str(cached_credentials.get('user_id')))

    contact_id = message.get('from')
    message_id = message.get('id')
    

    from app.schemas.messages import MessageExtractionRequest, Platform, UnifiedMessageContent, UnifiedMessageType
    platform_enum = Platform.WHATSAPP if platform == 'whatsapp' else Platform.INSTAGRAM

    feature_access = None
    user_subscription_id = str(user_info.get('user_id') or user_info.get('current_user_id'))
    if user_subscription_id and user_subscription_id != 'None':
        try:
            from app.services.credits_service import get_credits_service
            from app.db.session import get_db
            credits_service = await get_credits_service(get_db())
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
        else:  # Instagram
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
        #save the message in the database
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
    
    if extracted_message.token_count > 7000:
        #save message in the database and send notification to user 
        logger.error(f"Message too long: {extracted_message.token_count}")
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

 
        from app.schemas.messages import BatchMessageRequest
        batch_request = BatchMessageRequest(
            platform=platform_enum,
            account_id=account_id,
            contact_id=contact_id,
            message_data=message_data,
            conversation_message_id=save_response.conversation_message_id
        )

        success = await add_message_to_batch_unified(batch_request)

        if not success:
            logger.error('Failed to add to batch, deleting message from database')
            delete_message_from_db(save_response.conversation_message_id)
            return None

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
        cache_key = f"conversation:{social_account_id}:{customer_identifier}"
        cached = await conversation_cache.get(cache_key)
        if cached:
            return cached

        db = get_db()
        res_find = db.table('conversations').select('id').eq('social_account_id', social_account_id).eq('customer_identifier', customer_identifier).order('created_at', desc=True).limit(1).execute()
        rows = res_find.data or []
        if rows:
            conversation_id = str(rows[0]['id'])
            await conversation_cache.set(cache_key, conversation_id)
            return conversation_id
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
            if conversation_id:
                await conversation_cache.set(cache_key, conversation_id)
            return conversation_id
        return None
    except Exception as e:
        logger.error(f'Erreur gestion conversation: {e}')
        return None



def encode_image_to_base64(image_content: bytes) -> str:
    import base64
    return base64.b64encode(image_content).decode('utf-8')

def resize_image(image_content: bytes, width: int, height: int) -> bytes:
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(image_content))
    
    # Convertir en RGB si nécessaire (pour JPEG)
    if image.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')
    
    original_width, original_height = image.size
    
    # Toujours convertir en JPEG même si pas de redimensionnement
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
    Extrait les dimensions d'une image à partir de son contenu binaire
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
    Calcule approximativement les tokens basé sur la taille de l'image
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
    import httpx
    client = httpx.AsyncClient()
    url = f'https://graph.facebook.com/v23.0/{media_id}'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    r1 = await client.get(url, headers=headers)
    r1.raise_for_status()
    media_url = r1.json().get('url')
    response = await client.get(media_url, headers=headers)
    response.raise_for_status()
    return response.content

async def generate_smart_response(messages: List[HumanMessage], user_id: str, ai_settings: Dict[str, Any], conversation_id: str) -> Optional[Dict[str, Any]]:
    from app.services.rag_agent import create_rag_agent
    from app.deps.credit_tracker import CreditTracker, get_or_create_credit_tracker
    from app.services.credits_service import get_credits_service
    from app.db.session import get_db
    
    doc_lang = ai_settings.get('doc_lang', ["french"])
    system_prompt = SYSTEM_PROMPT
    if isinstance(doc_lang, list):
        doc_lang = ", ".join(doc_lang)
    local_system_prompt = system_prompt.format(doc_lang=doc_lang)
    model_name = 'x-ai/grok-4-fast:free'
    
    logger.info(f"🔍 DEBUG generate_smart_response - messages: {messages}")
    logger.info(f"🔍 DEBUG generate_smart_response - user_id: {user_id}")
    logger.info(f"🔍 DEBUG generate_smart_response - conversation_id: {conversation_id}")
    
    db = get_db()
    credits_service = await get_credits_service(db)
    credit_tracker = await get_or_create_credit_tracker(user_id, credits_service)
    
    agent = create_rag_agent(
        user_id, 
        model_name=model_name, 
        system_prompt=local_system_prompt,
        credit_tracker=credit_tracker
    )
    
    try:
        feature_access = await credits_service.get_feature_access(user_id)
        response = agent.graph.invoke(
            {"messages": messages},
            config={
                "configurable": {
                    "thread_id": f"1conversation:{conversation_id}day:{datetime.now().strftime('%Y-%m-%d')}",
                    "user_id": user_id,
                    "checkpoint_ns": f"user:{user_id}:conversation:{conversation_id}:{datetime.now().strftime('%Y-%m-%d')}"
                }
            }
        )
        
        await credit_tracker.finalize_batch(conversation_id=conversation_id)
        logger.info(f"✅ Credits finalisés pour batch: {credit_tracker.get_batch_info()}")
        
        logger.info(f"🔍 DEBUG generate_smart_response - response type: {type(response)}")
        logger.info(f"🔍 DEBUG generate_smart_response - response: {response}")
        return response
    except Exception as e:
        logger.error(f"🔍 DEBUG generate_smart_response - Exception: {e}")
        try:
            await credit_tracker.finalize_batch(conversation_id=conversation_id)
        except Exception as finalize_error:
            logger.error(f"Erreur finalisation batch après exception: {finalize_error}")
        return {"error": str(e)}


async def get_user_credentials_by_platform_account(platform: str, account_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        if platform not in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'whatsapp']:
            logger.error(f'Platform {platform} not supported')
            return None
        cache_key = f"credentials:{platform}:{account_id}"
        cached = await credentials_cache.get(cache_key)
        if cached:
            return cached

        db = get_db()
        res = db.table('social_accounts').select('*').eq('platform', platform).eq('account_id', account_id).eq('is_active', True).limit(1).execute()
        rows = res.data or []
        if rows:
            record = rows[0]
            await credentials_cache.set(cache_key, record)
            return record
        return None
    except Exception as e:
        logger.error(f'Error retrieving credentials {platform}:{account_id}: {e}')
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
        elif platform == 'instagram':
        
            service = InstagramService(user_credentials.get('access_token'), user_credentials.get('instagram_business_account_id'))

            if message_id:
                result = await service.send_typing_and_mark_read(contact_id, message_id)

                if result.get('success'):
                    logger.info(f'📱 Instagram: Sender actions réussis vers {contact_id} - {result.get("message")}')
                else:
                    logger.warning(f'❌ Échec sender actions Instagram vers {contact_id}: {result.get("error")}')

                return result.get('success', False)
            else:
                logger.warning('Message ID requis pour Instagram sender actions')
                return False
        else:
            logger.error(f'Plateforme non supportée pour indicateur de frappe: {platform}')
            return False
    except Exception as e:
        logger.error(f'Erreur envoi indicateur de frappe {platform}: {e}')
        return False

async def send_response(platform: str, user_credentials: Dict[str, Any], contact_id: str, content: str) -> bool:
    try:
        if platform == 'whatsapp':
            service = WhatsAppService(user_credentials.get('access_token'), user_credentials.get('account_id') or user_credentials.get('phone_number_id'))
            result = await service.send_text_message(to=contact_id, text=content, skip_validation=True)
            return bool(result.get('messages'))
        elif platform == 'instagram':
            service = InstagramService(user_credentials.get('access_token'), user_credentials.get('instagram_business_account_id'))
            result = await service.send_direct_message(contact_id, content)
            return result.get('success', False)
        else:
            return False
    except Exception as e:
        logger.error(f'Erreur lors de l\'envoi de réponse {platform}: {e}')
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
        logger.error(f'Erreur lors de la sauvegarde de réponse en BDD: {e}')





async def extract_message_content_unified(request: MessageExtractionRequest) -> Optional[UnifiedMessageContent]:
    """
    unified function to extract the content of WhatsApp and Instagram messages
    """
    try:
        if request.platform == Platform.WHATSAPP:
            return await extract_whatsapp_message_content(request.raw_message, request.user_credentials)
        elif request.platform == Platform.INSTAGRAM:
            return await extract_instagram_message_content(request.raw_message, request.user_credentials)
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

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f'Bearer {user_credentials.get("access_token")}'}
                response = await client.get(media_url, headers=headers)
                response.raise_for_status()
                media_content = response.content

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
        logger.warning(f"Type de message Instagram non supporté: {message_type}")
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
                error=f"Impossible de créer/récupérer la conversation pour {request.extracted_message.message_from}"
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
    import httpx
    url = f"https://graph.instagram.com/v23.0/{instagram_user_id}"
    params = {
        "fields": "name,username,profile_pic",
        "access_token": access_token
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
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

async def add_message_to_batch_unified(request: BatchMessageRequest) -> bool:
    """
    unified function to add a message to the batch of processing
    """
    try:
        success = await message_batcher.add_message_to_batch(
            platform=request.platform.value,
            account_id=request.account_id,
            contact_id=request.contact_id,
            message_data=request.message_data,
            conversation_message_id=request.conversation_message_id
        )
        return success
    except Exception as e:
        logger.error(f"Error adding to unified batch: {e}")
        return False