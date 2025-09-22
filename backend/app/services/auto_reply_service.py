from typing import Optional, Dict, Any
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class AutoReplyService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def get_user_auto_reply_settings(self, user_id: str, platform: str = 'whatsapp') -> Optional[Dict[str, Any]]:
        """Récupère les paramètres de réponse automatique d'un utilisateur"""
        try:
            response = self.supabase.table('auto_reply_settings').select('id, user_id, is_enabled, platform, settings, created_at, updated_at').eq('user_id', user_id).eq('platform', platform).execute()
            if response.data:
                return response.data[0]
            return await self.create_default_settings(user_id, platform)
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des paramètres auto-reply: {e}')
            return None

    async def create_default_settings(self, user_id: str, platform: str = 'whatsapp') -> Optional[Dict[str, Any]]:
        """Crée des paramètres par défaut pour un utilisateur"""
        try:
            default_settings = {'user_id': user_id, 'is_enabled': False, 'platform': platform, 'settings': {}}
            response = self.supabase.table('auto_reply_settings').insert(default_settings).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f'Erreur lors de la création des paramètres par défaut: {e}')
            return None

    async def update_auto_reply_settings(self, user_id: str, is_enabled: bool, platform: str = 'whatsapp', additional_settings: Optional[Dict[str, Any]] = None) -> bool:
        """Met à jour les paramètres de réponse automatique"""
        try:
            update_data = {'is_enabled': is_enabled}
            if additional_settings:
                update_data['settings'] = additional_settings
            response = self.supabase.table('auto_reply_settings').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
            if not response.data:
                await self.create_default_settings(user_id, platform)
                response = self.supabase.table('auto_reply_settings').update(update_data).eq('user_id', user_id).eq('platform', platform).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f'Erreur lors de la mise à jour des paramètres auto-reply: {e}')
            return False

    async def is_auto_reply_enabled(self, user_id: str, platform: str = 'whatsapp') -> bool:
        """Vérifie si les réponses automatiques sont activées pour un utilisateur"""
        try:
            settings = await self.get_user_auto_reply_settings(user_id, platform)
            return settings.get('is_enabled', False) if settings else False
        except Exception as e:
            logger.error(f'Erreur lors de la vérification de l\'état auto-reply: {e}')
            return False

    async def get_auto_reply_message(self, user_id: str, platform: str = 'whatsapp') -> Optional[str]:
        """Récupère le message de réponse automatique"""
        try:
            settings = await self.get_user_auto_reply_settings(user_id, platform)
            if settings and settings.get('is_enabled'):
                return settings.get('settings', {}).get('message', 'Merci pour votre message. Nous vous répondrons bientôt.')
            return None
        except Exception as e:
            logger.error(f'Erreur lors de la récupération du message auto-reply: {e}')
            return None

    async def set_auto_reply_message(self, user_id: str, message: str, platform: str = 'whatsapp') -> bool:
        """Définit le message de réponse automatique"""
        try:
            additional_settings = {'message': message}
            return await self.update_auto_reply_settings(user_id, True, platform, additional_settings)
        except Exception as e:
            logger.error(f'Erreur lors de la définition du message auto-reply: {e}')
            return False