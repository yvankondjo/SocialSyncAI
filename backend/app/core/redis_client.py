import logging
import asyncio
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Client Redis robuste avec pool de connexions, retry automatique et health checks.

    Fonctionnalités :
    - Pool de connexions configurable (min 10, max 50)
    - Retry automatique avec backoff exponentiel
    - Health checks périodiques
    - Fallback gracieux si Redis indisponible
    - Métriques de performance
    """

    def __init__(self):
        self.settings = get_settings()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._is_healthy = False
        self._last_health_check = 0
        self._health_check_interval = 30  # secondes

        # Métriques
        self._connection_attempts = 0
        self._successful_connections = 0
        self._failed_connections = 0

        # Initialiser la connexion
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialise le pool de connexions Redis."""
        try:
            # Configuration du retry
            retry = Retry(
                backoff=ExponentialBackoff(cap=10, base=1, jitter=True),
                retries=3
            )

            # Configuration du pool
            pool_kwargs = {
                'host': self.settings.REDIS_HOST,
                'port': self.settings.REDIS_PORT,
                'db': self.settings.REDIS_DB,
                'password': self.settings.REDIS_PASSWORD or None,
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_keepalive': True,
                'socket_keepalive_options': {redis.constants.KEEP_ALIVE_OPTIONS: 60},
                'retry': retry,
                'retry_on_timeout': True,
                'max_connections': 50,
                'encoding': 'utf-8',
            }

            # Si REDIS_URL est fourni, l'utiliser
            if self.settings.REDIS_URL:
                pool_kwargs['url'] = self.settings.REDIS_URL

            self._pool = ConnectionPool(**pool_kwargs)
            self._client = redis.Redis(connection_pool=self._pool)

            logger.info(f"✅ Pool Redis initialisé: {self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}")

        except Exception as e:
            logger.error(f"❌ Erreur initialisation pool Redis: {e}")
            self._pool = None
            self._client = None

    async def health_check(self) -> bool:
        """
        Effectue un health check de la connexion Redis.

        Returns:
            bool: True si Redis est accessible, False sinon
        """
        current_time = asyncio.get_event_loop().time()

        # Vérifier si on doit faire un health check
        if current_time - self._last_health_check < self._health_check_interval and self._is_healthy:
            return self._is_healthy

        self._last_health_check = current_time

        if not self._client:
            self._is_healthy = False
            return False

        try:
            # Ping simple pour vérifier la connexion
            result = await asyncio.wait_for(self._client.ping(), timeout=2.0)
            self._is_healthy = result is not None
            logger.debug("✅ Health check Redis réussi")
            return True

        except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
            logger.warning(f"⚠️ Health check Redis échoué: {e}")
            self._is_healthy = False
            return False
        except Exception as e:
            logger.error(f"❌ Erreur inattendue health check Redis: {e}")
            self._is_healthy = False
            return False

    async def get(self, key: str) -> Optional[str]:
        """Récupère une valeur depuis Redis."""
        if not await self._ensure_connection():
            return None

        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Erreur GET Redis {key}: {e}")
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Définit une valeur dans Redis."""
        if not await self._ensure_connection():
            return False

        try:
            return await self._client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Erreur SET Redis {key}: {e}")
            return False

    async def setex(self, key: str, time: int, value: str) -> bool:
        """Définit une valeur avec expiration dans Redis."""
        if not await self._ensure_connection():
            return False

        try:
            return await self._client.setex(key, time, value)
        except Exception as e:
            logger.error(f"Erreur SETEX Redis {key}: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        """Supprime une ou plusieurs clés Redis."""
        if not await self._ensure_connection():
            return 0

        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Erreur DELETE Redis {keys}: {e}")
            return 0

    async def incr(self, key: str) -> Optional[int]:
        """Incrémente une valeur numérique dans Redis."""
        if not await self._ensure_connection():
            return None

        try:
            return await self._client.incr(key)
        except Exception as e:
            logger.error(f"Erreur INCR Redis {key}: {e}")
            return None

    async def expire(self, key: str, time: int) -> bool:
        """Définit un TTL sur une clé Redis."""
        if not await self._ensure_connection():
            return False

        try:
            return await self._client.expire(key, time)
        except Exception as e:
            logger.error(f"Erreur EXPIRE Redis {key}: {e}")
            return False

    async def eval(self, script: str, keys: List[str], args: List[Any]) -> Any:
        """Exécute un script Lua dans Redis."""
        if not await self._ensure_connection():
            return None

        try:
            return await self._client.eval(script, len(keys), *(keys + args))
        except Exception as e:
            logger.error(f"Erreur EVAL Redis: {e}")
            return None

    async def pipeline(self):
        """Crée un pipeline Redis pour les opérations atomiques."""
        if not await self._ensure_connection():
            return None

        try:
            return self._client.pipeline()
        except Exception as e:
            logger.error(f"Erreur création pipeline Redis: {e}")
            return None

    async def _ensure_connection(self) -> bool:
        """
        S'assure que la connexion Redis est disponible.

        Returns:
            bool: True si la connexion est disponible, False sinon
        """
        if not self._client:
            logger.warning("Client Redis non initialisé")
            return False

        # Vérifier la santé de la connexion
        if not await self.health_check():
            logger.error("Connexion Redis non disponible")
            return False

        return True

    async def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques du client Redis."""
        return {
            'healthy': self._is_healthy,
            'connection_attempts': self._connection_attempts,
            'successful_connections': self._successful_connections,
            'failed_connections': self._failed_connections,
            'pool_size': self._pool.size if self._pool else 0,
            'last_health_check': self._last_health_check
        }

    async def close(self) -> None:
        """Ferme proprement la connexion Redis."""
        if self._client:
            await self._client.close()
            logger.info("✅ Connexion Redis fermée")

    @asynccontextmanager
    async def pipeline_context(self):
        """Context manager pour les opérations pipeline."""
        pipeline = await self.pipeline()
        if not pipeline:
            raise ConnectionError("Impossible de créer un pipeline Redis")

        try:
            yield pipeline
        finally:
            await pipeline.reset()


# Instance globale du client Redis
_redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Retourne l'instance globale du client Redis."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.health_check()
    return _redis_client


async def init_redis_client() -> RedisClient:
    """Initialise et retourne le client Redis avec health check."""
    client = await get_redis_client()

    # Health check initial
    if await client.health_check():
        logger.info("🎉 Client Redis initialisé avec succès")
    else:
        logger.warning("⚠️ Client Redis initialisé mais connexion indisponible")

    return client


async def close_redis_client() -> None:
    """Ferme le client Redis global."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None