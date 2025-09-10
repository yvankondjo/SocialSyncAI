from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, timezone
import logging

# Les schemas sont définis dans le router pour éviter les imports circulaires
from app.services.whatsapp_service import WhatsAppService
from app.services.instagram_service import InstagramService

logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_user_conversations(
        self, 
        user_id: str, 
        channel: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Récupère les conversations d'un utilisateur"""
        try:
            # Construire la requête de base
            query = self.supabase.table('conversations').select(
                '''
                id, customer_name, customer_identifier, last_message_at, unread_count,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                ),
                last_message: conversation_messages!conversation_messages_conversation_id_fkey (
                    content, created_at
                )
                '''
            )
            
            # Joindre avec social_accounts pour filtrer par user_id (nécessaire pour logique métier)
            query = query.eq('social_accounts.user_id', user_id)  # RLS assure sécurité supplémentaire
            
            # Filtrer par canal si spécifié
            if channel and channel != 'all':
                query = query.eq('social_accounts.platform', channel)
            
            # Ordonner par dernier message
            query = query.order('last_message_at', desc=True).limit(limit)
            
            response = query.execute()
            
            if not response.data:
                return []
            
            conversations = []
            for row in response.data:
                # Vérifier que l'utilisateur a accès à cette conversation
                social_account = row.get('social_accounts')
                if not social_account or social_account.get('user_id') != user_id:
                    continue
                
                conversation = {
                    'id': row['id'],
                    'channel': social_account['platform'],
                    'customer_name': row['customer_name'],
                    'customer_identifier': row['customer_identifier'],
                    'last_message_at': row['last_message_at'],
                    'last_message_snippet': row.get('last_message', [{}])[0].get('content', ''),
                    'unread_count': row.get('unread_count', 0),
                    'social_account_id': social_account['id']
                }
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des conversations pour l'utilisateur {user_id}: {e}")
            raise

    async def get_conversation_messages(
        self, 
        conversation_id: str, 
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Récupère les messages d'une conversation"""
        try:
            # Vérifier que l'utilisateur a accès à cette conversation
            access_check = self.supabase.table('conversations').select(
                'id, social_accounts: social_account_id (user_id)'
            ).eq('id', conversation_id).execute()
            
            if not access_check.data:
                raise ValueError("Conversation non trouvée")
            
            social_account = access_check.data[0].get('social_accounts')
            if not social_account or social_account.get('user_id') != user_id:
                raise ValueError("Accès non autorisé à cette conversation")
            
            # Récupérer les messages
            response = self.supabase.table('conversation_messages').select(
                'id, conversation_id, direction, content, created_at, sender_id, is_from_agent'
            ).eq('conversation_id', conversation_id).order('created_at', desc=False).limit(limit).execute()
            
            messages = []
            for row in response.data:
                message = {
                    'id': row['id'],
                    'conversation_id': row['conversation_id'],
                    'direction': row['direction'],
                    'content': row['content'],
                    'created_at': row['created_at'],
                    'sender_id': row['sender_id'],
                    'is_from_agent': row.get('is_from_agent', False)
                }
                messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des messages pour la conversation {conversation_id}: {e}")
            raise

    async def send_message(
        self, 
        conversation_id: str, 
        user_id: str, 
        content: str,
        message_type: str = 'text'
    ) -> Dict[str, Any]:
        """Envoie un message dans une conversation"""
        try:
            # Récupérer les détails de la conversation et du compte social
            conv_response = self.supabase.table('conversations').select(
                '''
                id, customer_identifier,
                social_accounts: social_account_id (
                    id, platform, account_id, access_token, user_id
                )
                '''
            ).eq('id', conversation_id).execute()
            
            if not conv_response.data:
                raise ValueError("Conversation non trouvée")
            
            conversation = conv_response.data[0]
            social_account = conversation.get('social_accounts')
            
            if not social_account or social_account.get('user_id') != user_id:
                raise ValueError("Accès non autorisé à cette conversation")
            
            platform = social_account['platform']
            customer_identifier = conversation['customer_identifier']
            
            # Envoyer le message selon la plateforme
            success = False
            error_message = None
            
            if platform == 'whatsapp':
                success = await self._send_whatsapp_message(
                    social_account['access_token'],
                    social_account['account_id'], 
                    customer_identifier,
                    content
                )
            elif platform == 'instagram':
                success = await self._send_instagram_message(
                    social_account['access_token'],
                    social_account['account_id'],  # Utiliser account_id au lieu de page_id
                    customer_identifier,
                    content
                )
            else:
                raise ValueError(f"Plateforme non supportée: {platform}")
            
            if not success:
                raise ValueError(f"Échec de l'envoi du message sur {platform}")
            
            # Enregistrer le message dans la base
            message_data = {
                'conversation_id': conversation_id,
                'direction': 'outbound',
                'message_type': message_type,
                'content': content,
                'is_from_agent': True,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            response = self.supabase.table('conversation_messages').insert(message_data).execute()
            
            if response.data:
                message_row = response.data[0]
                
                # Marquer automatiquement la conversation comme lue après envoi d'un message
                try:
                    await self.mark_conversation_as_read(conversation_id, user_id)
                except Exception as e:
                    logger.warning(f"Impossible de marquer la conversation comme lue: {e}")
                
                return {
                    'id': message_row['id'],
                    'conversation_id': message_row['conversation_id'],
                    'direction': message_row['direction'],
                    'content': message_row['content'],
                    'created_at': message_row['created_at'],
                    'is_from_agent': True
                }
            
            raise ValueError("Échec de l'enregistrement du message")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            raise

    async def _send_whatsapp_message(
        self, 
        access_token: str, 
        phone_number_id: str,
        to: str, 
        text: str
    ) -> bool:
        """Envoie un message WhatsApp"""
        try:
            async with WhatsAppService(access_token, phone_number_id) as service:
                result = await service.send_text_message(to, text)
                # Vérifier si le message a un ID (signe de succès)
                messages = result.get('messages', [])
                return len(messages) > 0 and messages[0].get('id') is not None
        except Exception as e:
            logger.error(f"Erreur WhatsApp: {e}")
            return False

    async def _send_instagram_message(
        self, 
        access_token: str, 
        account_id: str,
        recipient_id: str, 
        text: str
    ) -> bool:
        """Envoie un message Instagram"""
        try:
            async with InstagramService(access_token, account_id) as service:
                result = await service.send_direct_message(recipient_id, text)
                # Vérifier si le message a un ID (signe de succès)
                return result.get('id') is not None
        except Exception as e:
            logger.error(f"Erreur Instagram: {e}")
            return False

    async def mark_conversation_as_read(
        self, 
        conversation_id: str, 
        user_id: str
    ) -> bool:
        """Marque une conversation comme lue en utilisant la fonction SQL existante"""
        try:
            # Utiliser la fonction SQL existante mark_conversation_as_read
            result = self.supabase.rpc('mark_conversation_as_read', {
                'conversation_uuid': conversation_id
            }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du marquage comme lu: {e}")
            return False
