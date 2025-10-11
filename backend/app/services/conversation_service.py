
from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, timezone
import logging
import json
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService
from app.services.response_manager import get_signed_url
from app.services.media_cache_service import media_cache_service

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user_conversations(self, user_id: str, channel: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les conversations d'un utilisateur"""
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

                # Récupérer le vrai dernier message pour le snippet
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
            logger.error(f'Erreur lors de la récupération des conversations pour l\'utilisateur {user_id}: {e}')
            raise

    def _get_last_message_snippet(self, conversation_id: str) -> str:
        """Récupère le snippet du dernier message d'une conversation"""
        try:
            # Récupérer le dernier message (inbound ou outbound)
            response = self.supabase.table('conversation_messages').select(
                'content, message_type, direction'
            ).eq('conversation_id', conversation_id).order('created_at', desc=True).limit(1).execute()

            if not response.data:
                return ""

            message = response.data[0]
            content = message.get('content', '')

            # Si c'est du texte simple
            if message.get('message_type') == 'text' or not content:
                return content[:100] + ('...' if len(content) > 100 else '')

            # Si c'est du JSON (image avec texte)
            try:
                parsed_content = json.loads(content)
                if isinstance(parsed_content, list):
                    # Chercher le texte dans le contenu JSON
                    for item in parsed_content:
                        if item.get('type') == 'text' and item.get('text'):
                            text = item['text']
                            return text[:100] + ('...' if len(text) > 100 else '')
            except (json.JSONDecodeError, KeyError):
                pass

            # Fallback : retourner le contenu brut tronqué
            return str(content)[:100] + ('...' if len(str(content)) > 100 else '')

        except Exception as e:
            logger.warning(f'Erreur lors de la récupération du snippet pour la conversation {conversation_id}: {e}')
            return ""
    async def get_conversation_messages(self, conversation_id: str, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Récupère les messages d'une conversation"""
        try:
            response = self.supabase.table('conversation_messages').select(
                'id, conversation_id, external_message_id, direction, message_type, content, storage_object_name, '
                'media_type, sender_id, sender_name, sender_avatar_url, status, is_from_agent, agent_id, '
                'reply_to_message_id, metadata, created_at, updated_at'
            ).eq('conversation_id', conversation_id).order('created_at', desc=False).limit(limit).execute()
            
            messages = []
            for row in response.data:
                # Générer l'URL signée pour les médias si storage_object_name existe (avec cache Redis)
                media_url = None
                if row.get('storage_object_name'):
                    try:
                        # Utiliser le cache Redis pour éviter de régénérer les URLs
                        media_url = await media_cache_service.get_cached_signed_url(
                            storage_object_name=row['storage_object_name'],
                            bucket_id='message',
                            expires_in=3600*24  # 24 heures
                        )
                    except Exception as e:
                        logger.warning(f"Impossible de générer l'URL signée pour {row['storage_object_name']}: {e}")
                        # En cas d'erreur, on garde le storage_object_name comme fallback
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
                    'storage_object_name': row.get('storage_object_name'),  # Garder pour référence
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
            
            # try:
            #     await self.mark_conversation_as_read(conversation['id'], user_id)
            # except Exception as e:
            #     logger.warning(f'Impossible de marquer la conversation comme lue: {e}')
            
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