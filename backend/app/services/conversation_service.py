
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, timezone
import logging
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user_conversations(self, user_id: str, channel: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les conversations d'un utilisateur"""
        try:
            query = self.supabase.table('conversations').select('''
                id, customer_name, customer_identifier, last_message_at, unread_count, created_at, updated_at,
                social_account_id, external_conversation_id, status, priority, assigned_to, tags, metadata,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                ),
                last_message: conversation_messages!conversation_messages_conversation_id_fkey (
                    content, created_at, direction
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
                conversation = {
                    'id': row['id'],
                    'social_account_id': social_account['id'],
                    'external_conversation_id': row.get('external_conversation_id'),
                    'customer_identifier': row['customer_identifier'],
                    'customer_name': row.get('customer_name'),
                    'customer_avatar_url': row.get('customer_avatar_url'),
                    'status': row.get('status', 'open'),
                    'priority': row.get('priority', 'normal'),
                    'assigned_to': row.get('assigned_to', {}),
                    'tags': row.get('tags', 0),
                    'automation_disabled': False,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'channel': social_account['platform'],
                    'last_message_snippet': row.get('last_message', [{}])[0].get('content', '')
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
            logger.error(f'Erreur lors de la récupération des conversations pour l\'utilisateur {user_id}: {e}')
            raise
    def get_conversation_messages(self, conversation_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les messages d'une conversation"""
        try:
            response = self.supabase.table('conversation_messages').select(
                'id, conversation_id, external_message_id, direction, message_type, content, media_url, '
                'media_type, sender_id, sender_name, sender_avatar_url, status, is_from_agent, agent_id, '
                'reply_to_message_id, metadata, created_at, updated_at'
            ).eq('conversation_id', conversation_id).order('created_at', desc=False).limit(limit).execute()
            
            messages = []
            for row in response.data:
                message = {
                    'id': row['id'],
                    'conversation_id': row['conversation_id'],
                    'external_message_id': row.get('external_message_id'),
                    'direction': row['direction'],
                    'message_type': row.get('message_type', 'text'),
                    'content': row.get('content', ''),
                    'media_url': row.get('media_url'),
                    'media_type': row.get('media_type'),
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
            logger.error(f'Erreur lors de la récupération des messages pour la conversation {conversation_id}: {e}')
            raise
    async def send_message(self, content: str, customer_name: str, platform: str, message_type: str = 'text') -> Dict[str, Any]:
        """Envoie un message dans une conversation"""
        try:
            conv_response = self.supabase.table('conversations').select('''
                id, customer_identifier, customer_name,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                )
            ''').eq('customer_name', customer_name).eq('social_accounts.platform', platform).execute()
            
            if not conv_response.data:
                raise ValueError(f'Conversation non trouvée pour le client {customer_name} sur la plateforme {platform}')
            
            conversation = conv_response.data[0]
            social_account = conversation.get('social_accounts')
            customer_identifier = conversation['customer_identifier']
            
            logger.info(f'Envoi message - Plateforme: {platform}, Identifiant client: {customer_identifier}')
            
            if platform == 'whatsapp':
                normalized_phone = customer_identifier.replace(' ', '').replace('-', '').replace('.', '').replace('+', '')
                if normalized_phone.startswith('0'):
                    normalized_phone = '33' + normalized_phone[1:]
                elif not normalized_phone.startswith('33'):
                    normalized_phone = '33' + normalized_phone
                logger.info(f'Numéro original: \'{customer_identifier}\', normalisé: \'{normalized_phone}\'')
                customer_identifier = normalized_phone
            
            success = False
            if platform == 'whatsapp':
                success = await self._send_whatsapp_message(social_account['access_token'], social_account['account_id'], customer_identifier, content)
            elif platform == 'instagram':
                success = await self._send_instagram_message(social_account['access_token'], social_account['account_id'], customer_identifier, content)
            else:
                raise ValueError(f'Plateforme non supportée: {platform}')
            
            if not success:
                raise ValueError(f'Échec de l\'envoi du message sur {platform}')
            
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
            
            response = self.supabase.table('conversation_messages').insert(message_data).execute()
            if not response.data:
                raise ValueError('Échec de l\'enregistrement du message')
            
            try:
                await self.mark_conversation_as_read(conversation['id'])
            except Exception as e:
                logger.warning(f'Impossible de marquer la conversation comme lue: {e}')
            
            return response.data[0]
            
        except Exception as e:
            logger.error(f'Erreur lors de l\'envoi du message: {e}')
            raise

    async def _send_whatsapp_message(self, access_token: str, phone_number_id: str, to: str, text: str) -> bool:
        """Envoie un message WhatsApp"""
        try:
            async with WhatsAppService(access_token, phone_number_id) as service:
                result = await service.send_text_message(to, text)
                messages = result.get('messages', [])
                return len(messages) > 0 and messages[0].get('id') is not None
        except Exception as e:
            logger.error(f'Erreur WhatsApp: {e}')
            return False

    async def _send_instagram_message(self, access_token: str, account_id: str, recipient_id: str, text: str) -> bool:
        """Envoie un message Instagram"""
        try:
            async with InstagramService(access_token, account_id) as service:
                result = await service.send_direct_message(recipient_id, text)
                return result.get('id') is not None
        except Exception as e:
            logger.error(f'Erreur Instagram: {e}')
            return False

    async def mark_conversation_as_read(self, conversation_id: str) -> bool:
        """Marque une conversation comme lue en utilisant la fonction SQL existante"""
        try:
            result = self.supabase.rpc('mark_conversation_as_read', {'conversation_uuid': conversation_id}).execute()
            return True
        except Exception as e:
            logger.error(f'Erreur lors du marquage comme lu: {e}')
            return False