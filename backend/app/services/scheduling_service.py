from typing import List, Optional, Dict, Any
from supabase import Client
from datetime import datetime, timezone
import logging
import uuid
from app.schemas.scheduling import PlatformPreview, PlatformType, ScheduledPost, PostStatus
logger = logging.getLogger(__name__)

class SchedulingService:

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    pass
    pass

    async def generate_previews(self, content: str, platforms: List[PlatformType], media_urls: Optional[List[str]]=None, post_type: str='text') -> List[PlatformPreview]:
        """Génère des previews pour différentes plateformes"""
        previews = []
        for platform in platforms:
            if platform == PlatformType.INSTAGRAM:
                preview = self._generate_instagram_preview(content, media_urls)
            elif platform == PlatformType.REDDIT:
                preview = self._generate_reddit_preview(content, media_urls)
            elif platform == PlatformType.WHATSAPP:
                preview = self._generate_whatsapp_preview(content, media_urls)
            elif platform == PlatformType.LINKEDIN:
                preview = self._generate_linkedin_preview(content, media_urls)
            else:
                continue
            previews.append(preview)
        return previews

    def _generate_instagram_preview(self, content: str, media_urls: Optional[List[str]]) -> PlatformPreview:
        """Génère preview Instagram"""
        char_limit = 2200
        char_count = len(content)
        validation_errors = []
        if char_count > char_limit:
            validation_errors.append(f'Le contenu dépasse la limite de {char_limit} caractères')
        if not media_urls or len(media_urls) == 0:
            validation_errors.append('Instagram nécessite au moins une image')
        return PlatformPreview(platform=PlatformType.INSTAGRAM, preview_data={'content': content, 'media_urls': media_urls or [], 'format': 'square_image_with_caption', 'hashtags_visible': True}, character_count=char_count, character_limit=char_limit, is_valid=len(validation_errors) == 0, validation_errors=validation_errors)

    def _generate_reddit_preview(self, content: str, media_urls: Optional[List[str]]) -> PlatformPreview:
        """Génère preview Reddit"""
        char_limit = 40000
        char_count = len(content)
        validation_errors = []
        if char_count > char_limit:
            validation_errors.append(f'Le contenu dépasse la limite de {char_limit} caractères')
        title = content.split('\n')[0] if '\n' in content else content[:100]
        body = content[len(title):].strip() if len(content) > len(title) else ''
        return PlatformPreview(platform=PlatformType.REDDIT, preview_data={'title': title, 'body': body, 'media_urls': media_urls or [], 'format': 'title_and_text'}, character_count=char_count, character_limit=char_limit, is_valid=len(validation_errors) == 0, validation_errors=validation_errors)

    def _generate_whatsapp_preview(self, content: str, media_urls: Optional[List[str]]) -> PlatformPreview:
        """Génère preview WhatsApp"""
        char_limit = 4096
        char_count = len(content)
        validation_errors = []
        if char_count > char_limit:
            validation_errors.append(f'Le contenu dépasse la limite de {char_limit} caractères')
        return PlatformPreview(platform=PlatformType.WHATSAPP, preview_data={'content': content, 'media_urls': media_urls or [], 'format': 'message_with_media'}, character_count=char_count, character_limit=char_limit, is_valid=len(validation_errors) == 0, validation_errors=validation_errors)

    def _generate_linkedin_preview(self, content: str, media_urls: Optional[List[str]]) -> PlatformPreview:
        """Génère preview LinkedIn (STUB - toujours invalide)"""
        char_limit = 3000
        char_count = len(content)
        validation_errors = ["LinkedIn n'est pas encore disponible pour la planification"]
        return PlatformPreview(platform=PlatformType.LINKEDIN, preview_data={'content': content, 'media_urls': media_urls or [], 'format': 'professional_post', 'status': 'pending_setup'}, character_count=char_count, character_limit=char_limit, is_valid=False, validation_errors=validation_errors)
    pass
    pass
    pass

    async def schedule_post(self, user_id: str, content: str, platforms: List[PlatformType], scheduled_at: datetime, media_urls: Optional[List[str]]=None, post_type: str='text', metadata: Optional[Dict[str, Any]]=None) -> ScheduledPost:
        """Planifie un post"""
        try:
            post_id = str(uuid.uuid4())
            post_data = {'id': post_id, 'user_id': user_id, 'content': content, 'platforms': [p.value for p in platforms], 'scheduled_at': scheduled_at.isoformat(), 'status': PostStatus.SCHEDULED.value, 'media_urls': media_urls or [], 'post_type': post_type, 'metadata': metadata or {}, 'created_at': datetime.now(timezone.utc).isoformat(), 'updated_at': datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            logger.error(f'Erreur lors de la planification du post: {e}')
            raise
    pass

    async def get_calendar_posts(self, user_id: str, start_date: datetime, end_date: datetime, platforms: Optional[List[PlatformType]]=None) -> List[ScheduledPost]:
        """Récupère les posts du calendrier"""
        try:
            query = self.supabase.table('scheduled_posts').select('*').eq('user_id', user_id)
            query = query.gte('scheduled_at', start_date.isoformat())
            query = query.lte('scheduled_at', end_date.isoformat())
            if platforms:
                platform_values = [p.value for p in platforms]
        except Exception as e:
            logger.error(f'Erreur lors de la récupération des posts du calendrier: {e}')
            raise

    def get_scheduled_post(self, post_id: str, user_id: str) -> Optional[ScheduledPost]:
        """Récupère un post planifié spécifique"""
        try:
            response = self.supabase.table('scheduled_posts').select('*').eq('id', post_id).eq('user_id', user_id).execute()
            if response.data:
                return ScheduledPost(**response.data[0])
        except Exception as e:
            logger.error(f'Erreur lors de la récupération du post {post_id}: {e}')
            raise

    def cancel_scheduled_post(self, post_id: str, user_id: str) -> bool:
        """Annule un post planifié"""
        try:
            response = self.supabase.table('scheduled_posts').update({'status': PostStatus.CANCELLED.value, 'updated_at': datetime.now(timezone.utc).isoformat()}).eq('id', post_id).eq('user_id', user_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation du post {post_id}: {e}")
            raise