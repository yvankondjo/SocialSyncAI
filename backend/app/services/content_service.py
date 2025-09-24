from supabase import Client
from uuid import UUID
from typing import List
from app.schemas.content import ContentCreate, ContentUpdate

class ContentService:

    async def get_content_by_id(self, db: Client, content_id: UUID):
        """Récupère un contenu par son ID"""
        try:
            response = db.table('content').select('*').eq('id', str(content_id)).single().execute()
            return response.data
        except Exception as e:
            raise Exception(f'Erreur lors de la récupération du contenu: {e}')

    async def get_all_content_for_user(self, db: Client, user_id: UUID) -> List[dict]:
        """Récupère tous les contenus d'un utilisateur"""
        try:
            response = db.table('content').select('\n                *,\n                social_accounts:social_account_id (\n                    platform, username\n                )\n                ').eq('created_by', str(user_id)).order('created_at', desc=True).execute()
            return response.data or []
        except Exception as e:
            raise Exception(f'Erreur lors de la récupération des contenus: {e}')

    async def create_content(self, db: Client, content: ContentCreate, user_id: UUID):
        """Crée un nouveau contenu"""
        try:
            content_data = content.dict()
            content_data['created_by'] = str(user_id)
            response = db.table('content').insert(content_data).execute()
            if response.data:
                return response.data[0]
            raise Exception('Échec de la création du contenu')
        except Exception as e:
            raise Exception(f'Erreur lors de la création du contenu: {e}')

    async def update_content(self, db: Client, content_id: UUID, content: ContentUpdate):
        """Met à jour un contenu existant"""
        try:
            update_data = content.dict(exclude_unset=True)
            response = db.table('content').update(update_data).eq('id', str(content_id)).execute()
            if response.data:
                return response.data[0]
            raise Exception('Contenu non trouvé')
        except Exception as e:
            raise Exception(f'Erreur lors de la mise à jour du contenu: {e}')

    async def delete_content(self, db: Client, content_id: UUID):
        """Supprime un contenu"""
        try:
            response = db.table('content').delete().eq('id', str(content_id)).execute()
            if not response.data:
                raise Exception('Contenu non trouvé')
            return {'status': 'deleted', 'id': str(content_id)}
        except Exception as e:
            raise Exception(f'Erreur lors de la suppression du contenu: {e}')
content_service = ContentService()