"""
Instagram Profile Refresh
Endpoint pour rafraîchir les URLs d'avatars Instagram expirées
"""
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.session import get_authenticated_db
from app.core.security import get_current_user_id
import httpx
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/instagram", tags=["Instagram Profiles"])


@router.post("/refresh-avatars")
async def refresh_instagram_avatars(
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Rafraîchit les URLs d'avatars Instagram pour toutes les conversations Instagram
    de l'utilisateur connecté.

    Les URLs Instagram expirent après 24-48h, cette route permet de les rafraîchir.
    """
    try:
        # 1. Récupérer tous les comptes Instagram de l'utilisateur
        accounts_result = db.table('social_accounts').select(
            'id, account_id, access_token'
        ).eq('user_id', current_user_id).eq('platform', 'instagram').execute()

        if not accounts_result.data:
            return {
                "success": True,
                "message": "Aucun compte Instagram connecté",
                "refreshed": 0
            }

        total_refreshed = 0

        for account in accounts_result.data:
            access_token = account['access_token']
            social_account_id = account['id']

            # 2. Récupérer toutes les conversations Instagram pour ce compte
            conversations = db.table('conversations').select(
                'id, customer_identifier'
            ).eq('social_account_id', social_account_id).execute()

            if not conversations.data:
                continue

            # 3. Pour chaque conversation, récupérer le profil Instagram à jour
            async with httpx.AsyncClient() as client:
                for conv in conversations.data:
                    instagram_user_id = conv['customer_identifier']

                    try:
                        # Récupérer le profil Instagram via l'API
                        url = f"https://graph.instagram.com/{instagram_user_id}"
                        params = {
                            'fields': 'username,profile_pic',
                            'access_token': access_token
                        }

                        response = await client.get(url, params=params, timeout=10.0)

                        if response.status_code == 200:
                            profile = response.json()

                            # Mettre à jour l'avatar dans la DB
                            if 'profile_pic' in profile:
                                db.table('conversations').update({
                                    'customer_avatar_url': profile['profile_pic'],
                                    'customer_name': profile.get('username', conv.get('customer_name'))
                                }).eq('id', conv['id']).execute()

                                total_refreshed += 1
                                logger.info(f"Avatar rafraîchi pour conversation {conv['id']}")
                        else:
                            logger.warning(f"Erreur API Instagram pour user {instagram_user_id}: {response.status_code}")

                    except Exception as e:
                        logger.error(f"Erreur refresh profil {instagram_user_id}: {e}")
                        continue

        return {
            "success": True,
            "message": f"{total_refreshed} avatar(s) rafraîchi(s)",
            "refreshed": total_refreshed
        }

    except Exception as e:
        logger.error(f"Erreur refresh avatars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-avatar/{conversation_id}")
async def refresh_single_avatar(
    conversation_id: str,
    db: Client = Depends(get_authenticated_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Rafraîchit l'URL d'avatar pour une conversation spécifique
    """
    try:
        # 1. Récupérer la conversation
        conv_result = db.table('conversations').select(
            'id, customer_identifier, social_account_id'
        ).eq('id', conversation_id).execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation non trouvée")

        conv = conv_result.data[0]

        # 2. Récupérer le compte Instagram associé
        account_result = db.table('social_accounts').select(
            'access_token, user_id'
        ).eq('id', conv['social_account_id']).execute()

        if not account_result.data:
            raise HTTPException(status_code=404, detail="Compte social non trouvé")

        account = account_result.data[0]

        # Vérifier que c'est bien l'utilisateur connecté
        if account['user_id'] != current_user_id:
            raise HTTPException(status_code=403, detail="Non autorisé")

        # 3. Récupérer le profil Instagram
        instagram_user_id = conv['customer_identifier']
        access_token = account['access_token']

        async with httpx.AsyncClient() as client:
            url = f"https://graph.instagram.com/{instagram_user_id}"
            params = {
                'fields': 'username,profile_pic',
                'access_token': access_token
            }

            response = await client.get(url, params=params, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erreur API Instagram: {response.text}"
                )

            profile = response.json()

            # 4. Mettre à jour l'avatar
            if 'profile_pic' in profile:
                db.table('conversations').update({
                    'customer_avatar_url': profile['profile_pic'],
                    'customer_name': profile.get('username')
                }).eq('id', conversation_id).execute()

                return {
                    "success": True,
                    "message": "Avatar rafraîchi avec succès",
                    "avatar_url": profile['profile_pic']
                }
            else:
                raise HTTPException(status_code=400, detail="Pas d'avatar dans le profil")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur refresh avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))
