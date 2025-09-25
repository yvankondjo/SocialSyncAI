import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.services.message_batcher import MessageBatcher
from app.services.instagram_service import InstagramService
from app.services.whatsapp_service import WhatsAppService
from langchain_core.messages import HumanMessage
logger = logging.getLogger(__name__)
message_batcher = MessageBatcher()
def get_user_credentials_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table('social_accounts').select('id, account_id, access_token, display_name, username, expires_at').eq('platform', 'whatsapp').order('created_at', desc=True).limit(1).execute()
        rows = res.data or []
        if rows:
            row = rows[0]
            return {'user_id': user_id, 'social_account_id': str(row['id']), 'phone_number_id': row['account_id'], 'access_token': row['access_token'], 'display_name': row.get('display_name'), 'username': row.get('username')}
        logger.warning(f'No WhatsApp account found for user {user_id}')
        return None
    except Exception as e:
        logger.error(f'Error retrieving WhatsApp credentials: {e}')
        return None

def get_user_by_phone_number_id(phone_number_id: str) -> Optional[Dict[str, Any]]:
    from app.db.session import get_db
    try:
        db = get_db()
        res = db.table('social_accounts').select('id, user_id, access_token, display_name, username').eq('account_id', phone_number_id).limit(1).execute()
        rows = res.data or []
        if rows:
            row = rows[0]
            return {'user_id': str(row['user_id']), 'social_account_id': str(row['id']), 'account_id': phone_number_id, 'phone_number_id': phone_number_id, 'access_token': row['access_token'], 'display_name': row.get('display_name'), 'username': row.get('username')}
        logger.warning(f'No user found for phone_number_id: {phone_number_id}')
        return None
    except Exception as e:
        logger.error(f'Error retrieving WhatsApp user: {e}')
        return None

async def handle_messages_webhook_for_user(value: Dict[str, Any], user_info: Dict[str, Any]) -> None:
    for message in value.get('messages', []):
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
    platform = user_info.get('platform', 'whatsapp')
    account_id = user_info.get('account_id')
    user_credentials = get_user_credentials_by_platform_account(platform, account_id)

    contact_id = message.get('from')
    message_id = message.get('id')
    
    extracted_message = await extract_message_content(message, user_credentials)
    
    if extracted_message is None:
        if user_credentials and contact_id:
            result = await send_error_notification_to_user(contact_id, 'This Type of message is not supported yet', platform, user_credentials, message_id)
            if not result:
                logger.error(f'Error sending notification to user {contact_id}: This Type of message is not supported yet')
        else:
            logger.error(f'Impossible d\'envoyer notification: contact_id={contact_id}, user_credentials={bool(user_credentials)}')
        return None
    
    if extracted_message.get('token_count') > 7000:
        logger.error(f"Message trop long: {extracted_message.get('token_count')}")
        from langdetect import detect
        lang = detect(extracted_message.get('content')[:500])
        logger.error(f'Message language: {lang}')
        if lang != 'fr':
            logger.error(f'Message language not French: {lang}')
            if user_credentials:
                result = await send_error_notification_to_user(contact_id, 'error your message is too long', platform, user_credentials, message_id)
                if not result:
                    logger.error(f'Error sending notification to user {contact_id}: error your message is too long')
            return None
        else:
            if user_credentials:
                result = await send_error_notification_to_user(contact_id, 'Your message is too long', platform, user_credentials, message_id)
                if not result:
                    logger.error(f'Error sending notification to user {contact_id}: Your message is too long')
            return None
    
    try:
        conversation_message_info = save_incoming_message_to_db(extracted_message, user_info)

        if not conversation_message_info['conversation_message_id']:
            logger.error('Message not saved in database')
            return None

        success = await message_batcher.add_message_to_batch(
            platform,
            account_id,
            contact_id,
            conversation_message_info['conversation_message_data'],
            conversation_message_info['conversation_message_id']
        )

        if not success:
            logger.error('Failed to add to batch, deleting message from database')
            delete_message_from_db(conversation_message_info['conversation_message_id'])
            return None

        return conversation_message_info['conversation_message_id']
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

def save_incoming_message_to_db(extracted_message: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
    from app.db.session import get_db
    try:
        db = get_db()
        conversation_id = get_or_create_conversation(social_account_id=user_info['social_account_id'], customer_identifier=extracted_message.get('message_from'), customer_name=None)

        if not conversation_id:
            logger.error(f"Conversation non trouvée pour l'utilisateur {user_info['user_id']}")
            return {'conversation_message_id': None, 'conversation_message_data': None}
            
        if extracted_message.get('message_type') == 'image':
            caption = extracted_message.get('caption')
            content_text = caption if caption else '[Image]'
            external_id = extracted_message.get('message_id')
            logger.info(f"DEBUG SAVE IMAGE: external_message_id: {external_id}")
            if not external_id:
                logger.error(f"ERROR: No message_id found for image message: {extracted_message}")
                return {'conversation_message_id': None, 'conversation_message_data': None}
            message_data = {
                'conversation_id': conversation_id,
                'external_message_id': external_id,
                'direction': 'inbound',
                'message_type': extracted_message.get('message_type'),
                'content': content_text,
                'sender_id': extracted_message.get('message_from'),
                'storage_object_name': extracted_message.get('storage_object_name'),
                'media_type': extracted_message.get('media_type'),
                'status': 'received',
                'metadata': {
                    'role': 'user',
                    'content': extracted_message.get('content'),
                    'token_count': extracted_message.get('token_count'),
                    'storage_object_name': extracted_message.get('storage_object_name'),
                    'caption': extracted_message.get('caption'),

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
                'storage_object_name': None,
                'media_type': extracted_message.get('media_type', None),
                'status': 'received',
                'metadata': {
                    'role': 'user',
                    'content': extracted_message.get('content'),
                    'token_count': extracted_message.get('token_count')
                }
            }
        else:
            logger.error(f"Message type non supporté pas normale: {extracted_message.get('message_type')}")
            return {'conversation_message_id': None, 'conversation_message_data': None}
            
        try:
            res = db.table('conversation_messages').insert(message_data).execute()
            message_id = None
            if res and res.data:
                first = res.data[0]
                conversation_message_id = first.get('id') if first else None
            return {'conversation_message_id': conversation_message_id, 'conversation_message_data': message_data}

            
        except Exception as db_unique_error:
            if 'unique_external_message_id' in str(db_unique_error).lower():
                logger.info(f"Message {extracted_message.get('message_id')} déjà traité pour utilisateur {user_info['user_id']}")
                return {'conversation_message_id': None, 'conversation_message_data': None}
            else:
                raise db_unique_error
                
    except Exception as e:
        logger.error(f'Erreur sauvegarde message en BDD: {e}')
        return {'conversation_message_id': None, 'conversation_message_data': None}

def get_or_create_conversation(social_account_id: str, customer_identifier: str, customer_name: Optional[str]=None) -> Optional[str]:
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
        message_id = message.get('id')
        logger.info(f"DEBUG IMAGE: message_id from webhook: {message_id}")
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
            result = {
                'content': content,
                'token_count': total_tokens,
                'message_type': message_type,
                'message_id': message_id,
                'message_from': message.get('from'),
                'storage_object_name': saved_path,
                'media_type': message.get('image', {}).get('mime_type', 'image/jpeg'),
                'caption': caption,
                'media_url': image_url
            }
            logger.info(f"DEBUG IMAGE: returning message_id: {result['message_id']}")
            return result
        except Exception as e:
            logger.error(f'Erreur téléchargement image: {e}')
            return None
    # elif message_type == 'audio':
    #     media_id = message.get('audio', {}).get('id', '')
    #     try:
    #         media_content = await get_media_content(media_id, user_credentials.get('access_token'))
    #         audio_tokens = 50
    #         logger.info(f'Audio size: {len(media_content)} bytes, estimated tokens: {audio_tokens}')
    #         return {
    #             'content': '[Audio]',
    #             'token_count': audio_tokens,
    #             'message_type': message_type,
    #             'message_id': message.get('id'),
    #             'message_from': message.get('from')
    #         }
    #     except Exception as e:
    #         logger.error(f'Erreur téléchargement audio: {e}')
    #         return {
    #             'content': '[Audio]',
    #             'token_count': 10,
    #             'message_type': message_type,
    #             'message_id': message.get('id'),
    #             'message_from': message.get('from')
    #         }
    elif message_type in ['video', 'document', 'location', 'contacts', 'audio']:
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

async def generate_smart_response(messages: HumanMessage, user_id: str, ai_settings: Dict[str, Any], conversation_id: str) -> Optional[Dict[str, Any]]:
    from app.services.rag_agent import create_rag_agent
    system_prompt = ai_settings.get('system_prompt', '')
    # model_name = ai_settings.get('ai_model', 'gpt-4o-mini')
    model_name = 'google/gemini-2.5-flash'
    agent = create_rag_agent(user_id, model_name=model_name, system_prompt=system_prompt)
    response = agent.invoke(messages, conversation_id)
    return response


def get_user_credentials_by_platform_account(platform: str, account_id: str) -> Optional[Dict[str, Any]]:
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

def save_response_to_db(conversation_id: str, content: str, user_id: str) -> Optional[str]:
    from app.db.session import get_db
    try:
        db = get_db()
        payload = {'conversation_id': conversation_id, 'direction': 'outbound', 'content': content, 'message_type': 'text', 'is_from_agent': False, 'agent_id': user_id, 'sender_id': 'user', 'metadata': {'auto_generated': True, 'batch_response': True, 'role': 'assistant', 'content': content}}
        res = db.table('conversation_messages').insert(payload).execute()
        return res.data[0]['id'] if res.data else None
    except Exception as e:
        logger.error(f'Erreur lors de la sauvegarde de réponse en BDD: {e}')

async def refresh_image_urls_in_message(message: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(message.get('content'), list):
        storage_list = message.get('storage_object_name_list', [])
        storage_index = 0
        for item in message.get('content'):
            if item.get('type') == 'image_url' and storage_index < len(storage_list):
                item['image_url']['url'] = get_signed_url(storage_list[storage_index], bucket_id='message', expires_in=3600)
                storage_index += 1
    return message