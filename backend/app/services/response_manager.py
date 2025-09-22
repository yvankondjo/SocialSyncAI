import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.services.message_batcher import message_batcher
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)

async def get_user_credentials_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table('social_accounts').select('id, account_id, access_token, display_name, username, expires_at').eq('platform', 'whatsapp').order('created_at', desc=True).limit(1).execute()
        rows = res.data or []
        if rows:
            row = rows[0]
            return {'user_id': user_id, 'social_account_id': str(row['id']), 'phone_number_id': row['account_id'], 'access_token': row['access_token'], 'display_name': row.get('display_name'), 'username': row.get('username')}
        logger.warning(f'Aucun compte WhatsApp trouvé pour l\'utilisateur {user_id}')
        return None
    except Exception as e:
        logger.error(f'Erreur lors de la récupération des credentials WhatsApp: {e}')
        return None

async def get_user_by_phone_number_id(phone_number_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table('social_accounts').select('id, user_id, access_token, display_name, username').eq('account_id', phone_number_id).limit(1).execute()
        rows = res.data or []
        if rows:
            row = rows[0]
            return {'user_id': str(row['user_id']), 'social_account_id': str(row['id']), 'account_id': phone_number_id, 'phone_number_id': phone_number_id, 'access_token': row['access_token'], 'display_name': row.get('display_name'), 'username': row.get('username')}
        logger.warning(f'Aucun utilisateur trouvé pour phone_number_id: {phone_number_id}')
        return None
    except Exception as e:
        logger.error(f'Erreur lors de la récupération utilisateur WhatsApp: {e}')
        return None

async def handle_messages_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    for message in value.get('messages', []):
        await process_incoming_message_for_user(message, user_info)
    for status in value.get('statuses', []):
        await process_message_status_for_user(status, user_info)

async def send_error_notification_to_user(contact_id: str, message: str, platform: str, user_credentials: Dict[str, Any], message_id: str=None) -> str:
    await send_typing_indicator(platform, user_credentials, contact_id, message_id)
    logger.info(f'📝 Typing indicator + read receipt sent for error message to {platform}:{contact_id}')
    import time
    time.sleep(5)
    result = await send_response(platform, user_credentials, contact_id, message)
    if not result:
        logger.error(f'Erreur envoi notification à l\'utilisateur {contact_id}: {message}')
        return
    return result

async def process_incoming_message_for_user(message: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    platform = user_info.get('platform', 'whatsapp')
    account_id = user_info.get('account_id')
    user_credentials = await get_user_credentials_by_platform_account(platform, account_id)
    extracted_message = await extract_message_content(message, user_credentials)
    contact_id = extracted_message.get('message_from') if extracted_message else None
    message_id = extracted_message.get('message_id') if extracted_message else None
    
    if extracted_message is None:
        if user_credentials:
            result = await send_error_notification_to_user(contact_id, 'This Type of message is not supported yet', platform, user_credentials, message_id)
            if not result:
                logger.error(f'Erreur envoi notification à l\'utilisateur {contact_id}: This Type of message is not supported yet')
        return None
    
    if extracted_message.get('token_count') > 7000:
        logger.error(f"Message trop long: {extracted_message.get('token_count')}")
        from langdetect import detect
        lang = detect(extracted_message.get('content')[:500])
        logger.error(f'Langue du message: {lang}')
        if lang != 'fr':
            logger.error(f'Langue du message non française: {lang}')
            if user_credentials:
                result = await send_error_notification_to_user(contact_id, 'error your message is too long', platform, user_credentials, message_id)
                if not result:
                    logger.error(f'Erreur envoi notification à l\'utilisateur {contact_id}: error your message is too long')
            return None
        else:
            if user_credentials:
                result = await send_error_notification_to_user(contact_id, 'Votre message est trop long', platform, user_credentials, message_id)
                if not result:
                    logger.error(f'Erreur envoi notification à l\'utilisateur {contact_id}: Votre message est trop long')
            return None
    
    try:
        message_id = await save_incoming_message_to_db(extracted_message, user_info)
        return message_id
    except Exception as e:
        logger.error(f'Erreur sauvegarde message en BDD: {e}')
        return None

async def process_message_status_for_user(status: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    message_id = status.get('id')
    status_type = status.get('status')
    logger.info(f"Statut \'{status_type}\' pour message {message_id} (utilisateur: {user_info['user_id']})")
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

async def save_incoming_message_to_db(extracted_message: Dict[str, Any], user_info: Dict[str, Any]) -> Optional[str]:
    from app.db.session import get_db
    try:
        db = get_db()
        conversation_id = await get_or_create_conversation(social_account_id=user_info['social_account_id'], customer_identifier=extracted_message.get('message_from'), customer_name=None)
        
        if not conversation_id:
            return None
            
        if extracted_message.get('message_type') == 'image':
            caption = extracted_message.get('caption')
            message_data = {
                'conversation_id': conversation_id,
                'external_message_id': extracted_message.get('message_id'),
                'direction': 'inbound',
                'message_type': extracted_message.get('message_type'),
                'content': caption if caption else extracted_message.get('media_url'),
                'sender_id': extracted_message.get('message_from'),
                'media_url': extracted_message.get('media_url'),
                'media_type': extracted_message.get('media_type'),
                'status': 'received',
                'metadata': {
                    'role': 'user',
                    'content': extracted_message.get('content'),
                    'token_count': extracted_message.get('token_count'),
                    'media_path': extracted_message.get('media_path')
                }
            }
        elif extracted_message.get('message_type') in ['text', 'audio']:
            message_data = {
                'conversation_id': conversation_id,
                'external_message_id': extracted_message.get('message_id'),
                'direction': 'inbound',
                'message_type': extracted_message.get('message_type'),
                'content': extracted_message.get('content'),
                'sender_id': extracted_message.get('message_from'),
                'media_url': None,
                'media_type': extracted_message.get('media_type', None),
                'status': 'received',
                'metadata': {
                    'role': 'user',
                    'content': extracted_message.get('content'),
                    'token_count': extracted_message.get('token_count')
                }
            }
        else:
            return None
            
        try:
            res = db.table('conversation_messages').insert(message_data).execute()
            message_id = None
            if res and res.data:
                first = res.data[0]
                message_id = first.get('id') if first else None
            return message_id
        except Exception as db_unique_error:
            if 'unique_external_message_id' in str(db_unique_error).lower():
                logger.info(f"Message {extracted_message.get('message_id')} déjà traité pour utilisateur {user_info['user_id']}")
                return None
            else:
                raise db_unique_error
                
    except Exception as e:
        logger.error(f'Erreur sauvegarde message en BDD: {e}')
        return None
async def get_or_create_conversation(social_account_id: str, customer_identifier: str, customer_name: Optional[str]=None) -> Optional[str]:
    from app.db.session import get_db
    try:
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
            return str(first.get('id')) if first and first.get('id') else None
        return None
    except Exception as e:
        logger.error(f'Erreur gestion conversation: {e}')
        return None

async def add_message_to_conversation_message_groups(conversation_id: str, message: Dict[str, Any], model: str, user_id: str, message_count: int, token_count: int, message_ids: List[str]) -> Optional[str]:
    from app.db.session import get_db
    from datetime import datetime, timezone
    try:
        db = get_db()
        now = datetime.now(timezone.utc)
        uuid_message_ids = []
        for msg_id in message_ids:
            if msg_id:
                uuid_message_ids.append(str(msg_id))
        
        group_data = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'messages': message,
            'model': model,
            'message_count': message_count,
            'message_ids': uuid_message_ids,
            'token_count': token_count,
            'time_window_seconds': 15,
            'first_message_at': now.isoformat(),
            'last_message_at': now.isoformat(),
            'finalized_at': now.isoformat()
        }
        res = db.table('conversations_message_groups').insert(group_data).execute()
        if res.data:
            logger.info(f'Groupe de messages ajouté à la conversation {conversation_id}')
            return res.data[0]['id']
        return None
    except Exception as e:
        logger.error(f'Erreur lors de l\'ajout du groupe de messages: {e}')
        return None

def encode_image_to_base64(image_content: bytes) -> str:
    import base64
    return base64.b64encode(image_content).decode('utf-8')

def resize_image(image_content: bytes, width: int, height: int) -> bytes:
    from PIL import Image
    import io
    image = Image.open(io.BytesIO(image_content))
    original_width, original_height = image.size
    if original_width < width and original_height < height:
        return image_content
    resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    resized_image.save(output, format='JPEG', quality=85, optimize=True)
    logger.info(f'Image redimensionnée: {original_width}x{original_height} -> {width}x{height}')
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

def save_data_to_bucket(data: bytes, bucket_id: str, object_name: str) -> str:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.storage.from_(bucket_id).upload(object_name, data)
        if res.data and len(res.data) > 0:
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
        if res.data and len(res.data) > 0:
            return res.data[0]['signed_url']
        logger.error(f'Erreur génération URL signée pour {object_path}: {res}')
        return None
    except Exception as e:
        logger.error(f'Erreur lors de la génération de l\'URL signée: {e}')
        return None

async def extract_message_content(message: Dict[str, Any], user_credentials: Dict[str, Any]) -> Dict[str, Any]:
    import tiktoken
    enc = tiktoken.get_encoding('o200k_harmony')
    if not message:
        return None
    message_type = message.get('type', 'text')
    if message_type == 'text':
        return {
            'content': message.get('text', {}).get('body', ''),
            'token_count': len(enc.encode(message.get('text', {}).get('body', ''))),
            'message_type': message_type,
            'message_id': message.get('id'),
            'message_from': message.get('from')
        }
    if message_type == 'image':
        import uuid
        caption = message.get('image', {}).get('caption', '')
        media_id = message.get('image', {}).get('id', '')
        try:
            media_content = await get_media_content(media_id, user_credentials.get('access_token'))
            width, height = extract_image_dimensions(media_content)
            if width > 768 or height > 768:
                media_content = resize_image(media_content, 768, 768)
                width, height = (768, 768)
            image_tokens = calculate_image_tokens(width, height)
            object_path = f"{uuid.uuid4()}/{message.get('id')}.jpg"
            saved_path = save_data_to_bucket(media_content, bucket_id='message', object_name=object_path)
            if not saved_path:
                logger.error('Échec de la sauvegarde de l\'image dans Supabase Storage')
                return None
            image_url = get_signed_url(saved_path, bucket_id='message', expires_in=3600)
            if not image_url:
                logger.error('Échec de la génération de l\'URL signée')
                return None
            logger.info(f'Image caption: {caption}')
            logger.info(f'Image size: {len(media_content)} bytes, dimensions: {width}x{height}, tokens: {image_tokens}')
            if caption:
                text_tokens = len(enc.encode(f'[Image] {caption}'))
                content = [{'type': 'text', 'text': caption}, {'type': 'image_url', 'image_url': {'url': image_url}}]
                total_tokens = text_tokens + image_tokens
            else:
                content = [{'type': 'image_url', 'image_url': {'url': image_url}}]
                total_tokens = image_tokens
            return {
                'content': content,
                'token_count': total_tokens,
                'message_type': message_type,
                'message_id': message.get('id'),
                'message_from': message.get('from'),
                'media_url': image_url,
                'caption': caption,
                'media_path': saved_path
            }
        except Exception as e:
            logger.error(f'Erreur téléchargement image: {e}')
            return None
    elif message_type == 'audio':
        media_id = message.get('audio', {}).get('id', '')
        try:
            media_content = await get_media_content(media_id, user_credentials.get('access_token'))
            audio_tokens = 50
            logger.info(f'Audio size: {len(media_content)} bytes, estimated tokens: {audio_tokens}')
            return {
                'content': '[Audio]',
                'token_count': audio_tokens,
                'message_type': message_type,
                'message_id': message.get('id'),
                'message_from': message.get('from')
            }
        except Exception as e:
            logger.error(f'Erreur téléchargement audio: {e}')
            return {
                'content': '[Audio]',
                'token_count': 10,
                'message_type': message_type,
                'message_id': message.get('id'),
                'message_from': message.get('from')
            }
    elif message_type in ['video', 'document', 'location', 'contacts']:
        return None
    else:
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

async def generate_smart_response(messages: List[Dict[str, Any]], context: List[Dict[str, Any]], platform: str, ai_settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    from dotenv import load_dotenv
    import os
    from openai import OpenAI
    load_dotenv()
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
    openai = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    history = [{'role': ctx.get('message_data', {}).get('role', 'user'), 'content': ctx.get('message_data', {}).get('content', '')} for ctx in context]
    if not messages or not messages.get('message_data', {}).get('content'):
        return None
    new_messages = [{'role': messages.get('message_data', {}).get('role', 'user'), 'content': messages.get('message_data', {}).get('content', '')}]
    all_messages = [{'role': 'system', 'content': ai_settings.get('system_prompt')}, *history, *new_messages]
    logger.info('================================================================================')
    logger.info('🤖 LLM INPUT - Conversation Context')
    logger.info('================================================================================')
    logger.info(f"📊 Model: {ai_settings.get('ai_model')}")
    logger.info(f"🌡️ Temperature: {ai_settings.get('temperature')}")
    logger.info(f"📈 Top-p: {ai_settings.get('top_p')}")
    logger.info(f'📝 Total messages: {len(all_messages)}')
    logger.info(f'📚 History messages: {len(history)}')
    logger.info(f'💬 New messages: {len(new_messages)} (concatenated)')
    logger.info(f"📄 Concatenated content length: {len(messages.get('message_data', {}).get('content', ''))} characters")
    logger.info('--------------------------------------------------------------------------------')
    for i, msg in enumerate(all_messages):
        role = msg.get('role', 'user')
        role_emoji = '🤖' if role == 'system' else '👤' if role == 'user' else '🤖'
        content = msg.get('content', '')
        content_preview = content[:100] + '...' if len(content) > 100 else content
        logger.info(f'{role_emoji} [{i + 1}] {role.upper()}: {content_preview}')
    logger.info('--------------------------------------------------------------------------------')
    try:
        response = openai.chat.completions.create(
            model=ai_settings.get('ai_model'),
            messages=all_messages,
            temperature=ai_settings.get('temperature'),
            top_p=ai_settings.get('top_p'),
            max_tokens=1024
        )
        response_content = response.choices[0].message.content
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        logger.info('🤖 LLM OUTPUT - Response Generated')
        logger.info('--------------------------------------------------------------------------------')
        logger.info(f'📝 Response length: {len(response_content)} characters')
        logger.info(f'💬 Response content: {response_content}')
        
        return {
            'model': ai_settings.get('ai_model'),
            'response_content': response_content,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens
        }
    except Exception as e:
        logger.error(f'Erreur lors de la génération de la réponse: {e}')
        return None

async def get_user_credentials_by_platform_account(platform: str, account_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        if platform not in ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok', 'whatsapp']:
            logger.error(f'Platform {platform} not supported')
            return None
        db = get_db()
        res = db.table('social_accounts').select('*').eq('platform', platform).eq('account_id', account_id).eq('is_active', True).limit(1).execute()
        rows = res.data or []
        if rows:
            return rows[0]
        return None
    except Exception as e:
        logger.error(f'Erreur lors de la récupération des credentials {platform}:{account_id}: {e}')
        return None

async def send_typing_indicator(platform: str, user_credentials: Dict[str, Any], contact_id: str, message_id: str=None) -> bool:
    """
    Envoyer un indicateur de frappe via la plateforme appropriée
    """
    try:
        if platform == 'whatsapp':
            service = WhatsAppService(user_credentials.get('access_token'), user_credentials.get('account_id') or user_credentials.get('phone_number_id'))
            result = await service.send_typing_indicator(contact_id, message_id)
            return bool(result.get('messages'))
        elif platform == 'instagram':
            logger.info('Indicateur de frappe non supporté pour Instagram')
            return True
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
            service = InstagramService()
            result = await service.send_direct_message(user_credentials['instagram_business_account_id'], user_credentials['access_token'], contact_id, content)
            return result.get('success', False)
        else:
            return False
    except Exception as e:
        logger.error(f'Erreur lors de l\'envoi de réponse {platform}: {e}')
        return False

async def save_response_to_db(conversation_id: str, content: str, user_id: str) -> Optional[str]:
    from app.db.session import get_db
    try:
        db = get_db()
        payload = {'conversation_id': conversation_id, 'direction': 'outbound', 'content': content, 'message_type': 'text', 'is_from_agent': False, 'agent_id': user_id, 'sender_id': 'user', 'metadata': {'auto_generated': True, 'batch_response': True, 'role': 'assistant', 'content': content}}
        res = db.table('conversation_messages').insert(payload).execute()
        return res.data[0]['id'] if res.data else None
    except Exception as e:
        logger.error(f'Erreur lors de la sauvegarde de réponse en BDD: {e}')