
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, timezone
import logging
import json
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService
from app.services.messenger_service import MessengerService
from app.services.response_manager import get_signed_url
from app.services.media_cache_service import media_cache_service

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user_conversations(self, user_id: str, channel: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get the conversations for a user."""
        try:
            query = self.supabase.table('conversations').select('''
                id, customer_name, customer_identifier, customer_avatar_url, ai_mode, last_message_at, unread_count, created_at, updated_at,
                social_account_id, external_conversation_id, status, priority, assigned_to, tags, metadata,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                )
            ''')
            query = query.eq('social_accounts.user_id', user_id)
            if channel and channel != 'all':
                query = query.eq('social_accounts.platform', channel)
            query = query.order('last_message_at', desc=True).limit(limit * 2)
            response = query.execute()
            
            if not response.data:
                return []
            
            conversations = []
            for row in response.data:
                social_account = row.get('social_accounts')

                # Fetch the real last message for the snippet
                last_message_content = self._get_last_message_snippet(row['id'])

                conversation = {
                    'id': row['id'],
                    'social_account_id': social_account['id'],
                    'external_conversation_id': row.get('external_conversation_id'),
                    'customer_identifier': row['customer_identifier'],
                    'customer_name': row.get('customer_name'),
                    'customer_avatar_url': row.get('customer_avatar_url'),
                    'ai_mode': row.get('ai_mode', 'ON'),
                    'status': row.get('status', 'open'),
                    'priority': row.get('priority', 'normal'),
                    'assigned_to': row.get('assigned_to', {}),
                    'tags': row.get('tags', 0),
                    'automation_disabled': False,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'channel': social_account['platform'],
                    'last_message_snippet': last_message_content,
                    'last_message_at': row.get('last_message_at')
                }
                conversations.append(conversation)
            
            last_inbound_times = {}
            for conv in conversations:
                try:
                    inbound = self.supabase.table('conversation_messages').select('created_at, content').eq('conversation_id', conv['id']).eq('direction', 'inbound').order('created_at', desc=True).limit(1).execute()
                    if inbound.data:
                        last_inbound_times[conv['id']] = inbound.data[0]['created_at']
                    else:
                        last_inbound_times[conv['id']] = conv['last_message_at']
                except Exception:
                    last_inbound_times[conv['id']] = conv['last_message_at']
            
            conversations.sort(key=lambda c: last_inbound_times.get(c['id']) or '', reverse=True)
            conversations = conversations[:limit]
            return conversations
            
        except Exception as e:
            logger.error(f"Error fetching conversations for user {user_id}: {e}")
            raise

    def _get_last_message_snippet(self, conversation_id: str) -> str:
        """Get the snippet of the last message in a conversation."""
        try:
            # Fetch the last message (inbound or outbound)
            response = self.supabase.table('conversation_messages').select(
                'content, message_type, direction'
            ).eq('conversation_id', conversation_id).order('created_at', desc=True).limit(1).execute()

            if not response.data:
                return ""

            message = response.data[0]
            content = message.get('content', '')

            # Plain text
            if message.get('message_type') == 'text' or not content:
                return content[:100] + ('...' if len(content) > 100 else '')

            # JSON content (e.g. image with caption)
            try:
                parsed_content = json.loads(content)
                if isinstance(parsed_content, list):
                    # Find text items inside the JSON payload
                    for item in parsed_content:
                        if item.get('type') == 'text' and item.get('text'):
                            text = item['text']
                            return text[:100] + ('...' if len(text) > 100 else '')
            except (json.JSONDecodeError, KeyError):
                pass

            # Fallback: return truncated raw content
            return str(content)[:100] + ('...' if len(str(content)) > 100 else '')

        except Exception as e:
            logger.warning(f"Error fetching snippet for conversation {conversation_id}: {e}")
            return ""
    async def get_conversation_messages(self, conversation_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        try:
            response = self.supabase.table('conversation_messages').select(
                'id, conversation_id, external_message_id, direction, message_type, content, storage_object_name, '
                'media_type, sender_id, sender_name, sender_avatar_url, status, is_from_agent, agent_id, '
                'reply_to_message_id, metadata, created_at, updated_at'
            ).eq('conversation_id', conversation_id).order('created_at', desc=False).limit(limit).execute()
            
            messages = []
            for row in response.data:
                # Generate a signed URL for media if storage_object_name exists (with Redis cache)
                media_url = None
                if row.get('storage_object_name'):
                    try:
                        # Use Redis cache to avoid regenerating URLs
                        media_url = await media_cache_service.get_cached_signed_url(
                            storage_object_name=row['storage_object_name'],
                            bucket_id='message',
                            expires_in=3600*24  # 24 heures
                        )
                    except Exception as e:
                        logger.warning(f"Unable to generate signed URL for {row['storage_object_name']}: {e}")
                        # On error, keep storage_object_name as fallback
                        media_url = row['storage_object_name']

                message = {
                    'id': row['id'],
                    'conversation_id': row['conversation_id'],
                    'external_message_id': row.get('external_message_id'),
                    'direction': row['direction'],
                    'message_type': row.get('message_type', 'text'),
                    'content': row.get('content', ''),
                    'media_url': media_url,
                    'media_type': row.get('media_type'),
                    'storage_object_name': row.get('storage_object_name'),  # Keep for reference
                    'sender_id': row.get('sender_id'),
                    'sender_name': row.get('sender_name'),
                    'sender_avatar_url': row.get('sender_avatar_url'),
                    'status': row.get('status'),
                    'is_from_agent': row.get('is_from_agent', False),
                    'agent_id': row.get('agent_id'),
                    'reply_to_message_id': row.get('reply_to_message_id'),
                    'metadata': row.get('metadata', {}),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
                messages.append(message)
            return messages
        except Exception as e:
            logger.error(f"Error fetching messages for conversation {conversation_id}: {e}")
            raise
    async def send_message(self, content: str, customer_name: str, platform: str, message_type: str = 'text', user_id: str = None) -> Dict[str, Any]:
        """Send a message in a conversation."""
        try:
            query = self.supabase.table('conversations').select('''
                id, customer_identifier, customer_name,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                )
            ''').eq('customer_name', customer_name).eq('social_accounts.platform', platform)
            
            if user_id:
                query = query.eq('social_accounts.user_id', user_id)
            
            conv_response = query.execute()
            
            if not conv_response.data:
                raise ValueError(f"Conversation not found for customer {customer_name} on platform {platform}")
            
            conversation = conv_response.data[0]
            social_account = conversation.get('social_accounts')
            
            if not social_account:
                raise ValueError("Social account not found for conversation")
            
            if user_id and social_account.get('user_id') != user_id:
                raise ValueError("You don't have access to this conversation")
            
            customer_identifier = conversation['customer_identifier']
            
            logger.info(f"Sending message - Platform: {platform}, Customer identifier: {customer_identifier}")
            
            if platform == 'whatsapp':
                normalized_phone = customer_identifier.replace(' ', '').replace('-', '').replace('.', '').replace('+', '')
                if normalized_phone.startswith('0'):
                    normalized_phone = '33' + normalized_phone[1:]
                elif not normalized_phone.startswith('33'):
                    normalized_phone = '33' + normalized_phone
                logger.info(f"Original number: '{customer_identifier}', normalized: '{normalized_phone}'")
                customer_identifier = normalized_phone
            
            success = False
            if platform == 'whatsapp':
                success = await self._send_whatsapp_message(social_account['access_token'], social_account['account_id'], customer_identifier, content)
            elif platform == 'instagram':
                success = await self._send_instagram_message(social_account['access_token'], social_account['account_id'], customer_identifier, content)
            elif platform == 'messenger':
                success = await self._send_messenger_message(social_account['access_token'], social_account['account_id'], customer_identifier, content)
            else:
                raise ValueError(f"Unsupported platform: {platform}")
            
            if not success:
                raise ValueError(f"Failed to send message on {platform}")
            
            message_data = {
                'conversation_id': conversation['id'],
                'direction': 'outbound',
                'message_type': message_type,
                'content': content,
                'is_from_agent': True,
                'status': 'sent',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"💾 Attempting to save message for conversation {conversation['id']}")
            logger.debug(f"💾 Message data: {message_data}")
            
            try:
                response = self.supabase.table('conversation_messages').insert(message_data).execute()
                logger.info(f"💾 Insert response: {response}")
                
                if not response.data:
                    logger.error("❌ Save failed: empty response")
                    raise ValueError("Failed to save message - empty response")
                
                logger.info(f"✅ Message saved successfully: {response.data[0].get('id')}")
                return response.data[0]
            except Exception as insert_error:
                logger.error(f"❌ Error inserting message: {insert_error}", exc_info=True)
                raise ValueError(f"Failed to save message: {str(insert_error)}")
            
            # try:
            #     await self.mark_conversation_as_read(conversation['id'], user_id)
            # except Exception as e:
            #     logger.warning(f"Unable to mark conversation as read: {e}")
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def _send_whatsapp_message(self, access_token: str, phone_number_id: str, to: str, text: str) -> bool:
        """Envoie un message WhatsApp"""
        try:
            async with WhatsAppService(access_token, phone_number_id) as service:
                result = await service.send_text_message(to, text)
                messages = result.get('messages', [])
                success = len(messages) > 0 and messages[0].get('id') is not None
                if success:
                    logger.info(f'✅ WhatsApp message sent successfully: {messages[0].get("id")}')
                else:
                    logger.error(f'❌ WhatsApp send failed: {result}')
                return success
        except Exception as e:
            logger.error(f'❌ Erreur WhatsApp: {e}', exc_info=True)
            return False

    async def _send_instagram_message(self, access_token: str, account_id: str, recipient_id: str, text: str) -> bool:
        """Envoie un message Instagram"""
        try:
            async with InstagramService(access_token, account_id) as service:
                result = await service.send_direct_message(recipient_id, text)
                # send_direct_message retourne {'success': True, 'message_id': ..., 'result': {...}}
                # Vérifier success ET message_id
                success = result.get('success', False)
                message_id = result.get('message_id') or result.get('result', {}).get('message_id')
                logger.info(f'📤 Instagram send result: success={success}, message_id={message_id}, full_result={result}')
                if not success:
                    logger.error(f'❌ Instagram send failed: {result}')
                    return False
                if not message_id:
                    logger.error(f'❌ Instagram send succeeded but no message_id returned: {result}')
                    return False
                logger.info(f'✅ Instagram message sent successfully: message_id={message_id}')
                return True
        except Exception as e:
            logger.error(f'❌ Erreur Instagram: {e}', exc_info=True)
            return False

    async def _send_messenger_message(self, access_token: str, page_id: str, recipient_psid: str, text: str) -> bool:
        """Envoie un message Messenger"""
        try:
            async with MessengerService(access_token, page_id) as service:
                result = await service.send_message(recipient_psid, text)
                success = result.get('success', False)
                message_id = result.get('message_id')
                logger.info(f'📤 Messenger send result: success={success}, message_id={message_id}, full_result={result}')
                if not success:
                    logger.error(f'❌ Messenger send failed: {result}')
                    return False
                if not message_id:
                    logger.error(f'❌ Messenger send succeeded but no message_id returned: {result}')
                    return False
                logger.info(f'✅ Messenger message sent successfully: message_id={message_id}')
                return True
        except Exception as e:
            logger.error(f'❌ Erreur Messenger: {e}', exc_info=True)
            return False

    async def mark_conversation_as_read(self, conversation_id: str, user_id: str) -> bool:
        """Marque une conversation comme lue en utilisant la fonction SQL existante"""
        try:
            conversation_check = self.supabase.table('conversations').select('id').eq('id', conversation_id).execute()
            if not conversation_check.data:
                logger.warning(f"Conversation {conversation_id} non trouvée")
                return False
            auth_check = self.supabase.table('conversations').select(
                'social_accounts!inner(user_id)'
            ).eq('id', conversation_id).eq('social_accounts.user_id', user_id).execute()

            if not auth_check.data:
                logger.warning(f"Utilisateur {user_id} n'a pas accès à la conversation {conversation_id}")
                return False

            result = self.supabase.rpc('mark_conversation_as_read', {'conversation_uuid': conversation_id}).execute()
            return True
        except Exception as e:
            logger.error(f'Erreur lors du marquage comme lu: {e}')
            return False