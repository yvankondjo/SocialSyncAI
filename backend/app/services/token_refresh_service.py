"""
Service pour la gestion du rafraîchissement des tokens (manuel)
Simplifié - pas de tâche automatique
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.db.session import get_db
from app.services.social_auth_service import social_auth_service
import logging

logger = logging.getLogger(__name__)

class TokenRefreshService:
    def __init__(self):
        self.db = None
    
    async def check_expired_tokens(self, user_id: str):
        """Vérifie si un utilisateur a des tokens expirés et retourne la liste."""
        try:
            db = next(get_db())
            
            # Récupérer les comptes expirés pour cet utilisateur
            now = datetime.now(timezone.utc)
            
            response = db.table("social_accounts").select("*").filter(
                "user_id", "eq", user_id
            ).filter(
                "token_expires_at", "lt", now.isoformat()
            ).filter(
                "is_active", "eq", True
            ).execute()
            
            return response.data
                
        except Exception as e:
            logger.error(f"Error checking expired tokens: {e}")
            return []
    
    async def _refresh_account_token(self, account: Dict[str, Any]):
        """Rafraîchit le token d'un compte spécifique."""
        try:
            platform = account["platform"]
            refresh_token = account["refresh_token"]
            
            if not refresh_token:
                logger.warning(f"No refresh token for account {account['id']} ({platform})")
                return
            
            # Rafraîchir selon la plateforme
            if platform == "reddit":
                new_token_data = await social_auth_service.refresh_reddit_token(refresh_token)
            elif platform == "twitter":
                # TODO: Implémenter refresh Twitter
                logger.info(f"Twitter refresh not implemented yet for account {account['id']}")
                return
            else:
                logger.info(f"Refresh not supported for platform {platform}")
                return
            
            # Calculer la nouvelle date d'expiration
            expires_in = new_token_data.get("expires_in", 3600)
            new_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            # Mettre à jour en base
            update_data = {
                "access_token": new_token_data["access_token"],
                "token_expires_at": new_expiry.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.db.table("social_accounts").update(update_data).eq(
                "id", account["id"]
            ).execute()
            
            logger.info(f"Successfully refreshed token for {platform} account {account['id']}")
            
        except Exception as e:
            logger.error(f"Failed to refresh token for account {account['id']}: {e}")
            
            # Marquer le compte comme inactif si le refresh échoue
            self.db.table("social_accounts").update({
                "is_active": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", account["id"]).execute()
    
    async def refresh_specific_token(self, account_id: str) -> bool:
        """Rafraîchit le token d'un compte spécifique à la demande."""
        try:
            db = next(get_db())
            
            response = db.table("social_accounts").select("*").eq("id", account_id).execute()
            
            if not response.data:
                logger.error(f"Account {account_id} not found")
                return False
            
            account = response.data[0]
            await self._refresh_account_token(account)
            return True
            
        except Exception as e:
            logger.error(f"Error refreshing specific token {account_id}: {e}")
            return False

# Instance globale
token_refresh_service = TokenRefreshService()
