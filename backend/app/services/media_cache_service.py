import logging
import os
from typing import Optional
import redis.asyncio as redis
from app.services.response_manager import get_signed_url

logger = logging.getLogger(__name__)

class MediaCacheService:
    """
    Service de cache pour les URLs signées des médias
    
    Utilise Redis pour éviter de régénérer les URLs signées
    TTL par défaut: 23h (pour éviter l'expiration des URLs de 24h)
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_pool = None
        self.default_ttl = 23 * 3600  # 23 heures en secondes
        
    async def get_redis(self) -> redis.Redis:
        """Obtenir une connexion Redis depuis le pool"""
        if not self._redis_pool:
            self._redis_pool = redis.ConnectionPool.from_url(
                self.redis_url, 
                decode_responses=True, 
                max_connections=20
            )
        return redis.Redis(connection_pool=self._redis_pool)
    
    def _get_cache_key(self, storage_object_name: str) -> str:
        """Générer la clé de cache pour un objet de stockage"""
        return f"media:signed_url:{storage_object_name}"
    
    async def get_cached_signed_url(
        self, 
        storage_object_name: str, 
        bucket_id: str = 'message',
        expires_in: int = None
    ) -> Optional[str]:
        """
        Récupérer une URL signée depuis le cache ou la générer
        
        Args:
            storage_object_name: Nom de l'objet dans le stockage
            bucket_id: ID du bucket (défaut: 'message')
            expires_in: Durée de validité en secondes (défaut: 24h)
            
        Returns:
            URL signée ou None en cas d'erreur
        """
        if expires_in is None:
            expires_in = 24 * 3600  # 24 heures
            
        cache_key = self._get_cache_key(storage_object_name)
        
        try:
            redis_client = await self.get_redis()
            
            # Vérifier le cache
            cached_url = await redis_client.get(cache_key)
            if cached_url:
                logger.debug(f"URL signée trouvée en cache pour {storage_object_name}")
                return cached_url
            
            # Générer nouvelle URL signée
            logger.debug(f"Génération nouvelle URL signée pour {storage_object_name}")
            signed_url = get_signed_url(
                object_path=storage_object_name,
                bucket_id=bucket_id,
                expires_in=expires_in
            )
            
            if not signed_url:
                logger.error(f"Impossible de générer l'URL signée pour {storage_object_name}")
                return None
            
            # Mettre en cache avec TTL légèrement inférieur à l'expiration
            cache_ttl = min(self.default_ttl, expires_in - 3600)  # 1h de marge
            if cache_ttl > 0:
                await redis_client.setex(cache_key, cache_ttl, signed_url)
                logger.debug(f"URL signée mise en cache pour {storage_object_name} (TTL: {cache_ttl}s)")
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération/génération de l'URL signée pour {storage_object_name}: {e}")
            # En cas d'erreur Redis, essayer de générer directement
            try:
                return get_signed_url(
                    object_path=storage_object_name,
                    bucket_id=bucket_id,
                    expires_in=expires_in
                )
            except Exception as fallback_error:
                logger.error(f"Erreur fallback pour {storage_object_name}: {fallback_error}")
                return None
    
    async def invalidate_cache(self, storage_object_name: str) -> bool:
        """
        Invalider le cache pour un objet spécifique
        
        Args:
            storage_object_name: Nom de l'objet dans le stockage
            
        Returns:
            True si supprimé avec succès, False sinon
        """
        cache_key = self._get_cache_key(storage_object_name)
        
        try:
            redis_client = await self.get_redis()
            result = await redis_client.delete(cache_key)
            logger.debug(f"Cache invalidé pour {storage_object_name}: {bool(result)}")
            return bool(result)
        except Exception as e:
            logger.error(f"Erreur lors de l'invalidation du cache pour {storage_object_name}: {e}")
            return False
    
    async def get_batch_signed_urls(
        self, 
        storage_object_names: list[str], 
        bucket_id: str = 'message',
        expires_in: int = None
    ) -> dict[str, Optional[str]]:
        """
        Récupérer plusieurs URLs signées en batch
        
        Args:
            storage_object_names: Liste des noms d'objets
            bucket_id: ID du bucket (défaut: 'message')
            expires_in: Durée de validité en secondes (défaut: 24h)
            
        Returns:
            Dictionnaire {storage_object_name: signed_url}
        """
        results = {}
        
        for storage_object_name in storage_object_names:
            signed_url = await self.get_cached_signed_url(
                storage_object_name, bucket_id, expires_in
            )
            results[storage_object_name] = signed_url
            
        return results
    
    async def close(self):
        """Fermer les connexions Redis"""
        if self._redis_pool:
            await self._redis_pool.disconnect()

# Instance globale du service
media_cache_service = MediaCacheService()
