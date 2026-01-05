import logging
import asyncio
import ssl
import os
import socket
import logging
from typing import Optional, Any, Dict, List
from contextlib import asynccontextmanager
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError, ResponseError

def _ensure_asyncio_constants():
    """Shim pour exposer redis.constants dans redis.asyncio"""
    try:
        if not hasattr(redis, 'constants'):
            try:
                import redis.constants as constants
                redis.constants = constants
            except ImportError:
                class Constants:
                    KEEP_ALIVE_OPTIONS = socket.TCP_KEEPIDLE if hasattr(socket, 'TCP_KEEPIDLE') else None
                redis.constants = Constants()
    except Exception as e:
        logger.warning(f"⚠️ Impossible de patcher redis.asyncio.constants : {e}")

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisRateLimitError(RuntimeError):
    """Raised when Upstash rejects commands because the max request quota is exhausted."""


def _is_rate_limit_error(exc: Exception) -> bool:
    """Detect Upstash rate-limit errors and return True when the quota is exhausted."""
    message = str(exc).lower()
    return "max requests limit exceeded" in message


def _build_keepalive_options() -> Dict[int, int]:
    """Return portable TCP keepalive options supported by the current OS."""
    options: Dict[int, int] = {}

    if hasattr(socket, "TCP_KEEPIDLE"):
        options[socket.TCP_KEEPIDLE] = 60
    if hasattr(socket, "TCP_KEEPINTVL"):
        options[socket.TCP_KEEPINTVL] = 15
    if hasattr(socket, "TCP_KEEPCNT"):
        options[socket.TCP_KEEPCNT] = 4

    return options


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
            _ensure_asyncio_constants()
            
            # Configuration du retry
            retry = Retry(
                backoff=ExponentialBackoff(cap=10, base=1),
                retries=3
            )

            # Utiliser resolve_redis_url() pour garantir la cohérence avec les workers
            from app.core.config import resolve_redis_url
            redis_url = resolve_redis_url()
            
            if redis_url:
                # Parser l'URL et retirer ssl_cert_reqs de la query string pour éviter le conflit
                parsed = urlparse(redis_url)
                query_params = parse_qs(parsed.query)
                
                # Retirer ssl_cert_reqs de la query string
                if 'ssl_cert_reqs' in query_params:
                    del query_params['ssl_cert_reqs']
                
                # Reconstruire l'URL sans ssl_cert_reqs
                new_query = urlencode(query_params, doseq=True)
                clean_url = urlunparse((
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment
                ))
                
                # Pour les URLs non-SSL (redis://), ne pas passer ssl_cert_reqs
                # Pour les URLs SSL (rediss://), passer ssl_cert_reqs=None
                kwargs = {
                    'decode_responses': True,
                    'socket_connect_timeout': 5,
                    'socket_keepalive': True,
                    'retry': retry,
                    'retry_on_timeout': True,
                    'max_connections': 2,
                    'encoding': 'utf-8',
                }
                
                if redis.constants.KEEP_ALIVE_OPTIONS is not None:
                    kwargs['socket_keepalive_options'] = {redis.constants.KEEP_ALIVE_OPTIONS: 60}
                
                if parsed.scheme == 'rediss':
                    kwargs['ssl_cert_reqs'] = None
                
                self._client = redis.Redis.from_url(clean_url, **kwargs)
                # Récupérer le pool du client pour compatibilité avec le reste du code
                self._pool = self._client.connection_pool
                ssl_info = "SSL configuré" if parsed.scheme == 'rediss' else "non-SSL"
                logger.info(f"✅ Pool Redis initialisé via REDIS_URL ({ssl_info})")
            else:
                # Configuration du pool optimisée pour 30MB RAM (fallback si pas d'URL)
                pool_kwargs = {
                    'host': self.settings.REDIS_HOST,
                    'port': self.settings.REDIS_PORT,
                    'db': self.settings.REDIS_DB,
                    'password': self.settings.REDIS_PASSWORD or None,
                    'decode_responses': True,
                    'socket_connect_timeout': 5,
                    'socket_keepalive': True,
                    'retry': retry,
                    'retry_on_timeout': True,
                    'max_connections': 2,
                    'encoding': 'utf-8',
                }
                
                if redis.constants.KEEP_ALIVE_OPTIONS is not None:
                    pool_kwargs['socket_keepalive_options'] = {redis.constants.KEEP_ALIVE_OPTIONS: 60}
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

        except (ConnectionError, TimeoutError, asyncio.TimeoutError, ResponseError) as e:
            if _is_rate_limit_error(e):
                logger.error("🚦 Limite de requêtes Upstash atteinte : suspension temporaire des appels Redis")
                self._is_healthy = False
                return False

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


# Helpers pour créer des clients Redis avec SSL correctement configuré
# Ces fonctions écrasent ssl_cert_reqs de l'URL pour éviter l'erreur "Invalid SSL Certificate Requirements Flag"
def get_redis_sync() -> redis.Redis:
    """
    Crée un client Redis synchrone avec SSL correctement configuré.
    
    Écrase ssl_cert_reqs de l'URL pour éviter l'erreur avec redis-py.
    """
    import redis as redis_sync
    from app.core.config import resolve_redis_url
    
    redis_url = resolve_redis_url()
    
    # Parser l'URL et retirer ssl_cert_reqs de la query string
    parsed = urlparse(redis_url)
    query_params = parse_qs(parsed.query)
    
    # Retirer ssl_cert_reqs de la query string pour éviter le conflit
    if 'ssl_cert_reqs' in query_params:
        del query_params['ssl_cert_reqs']
    
    # Reconstruire l'URL sans ssl_cert_reqs
    new_query = urlencode(query_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    # Pour les URLs non-SSL (redis://), ne pas passer ssl_cert_reqs
    # Pour les URLs SSL (rediss://), passer ssl_cert_reqs=None
    kwargs = {
        'decode_responses': True,
    }
    
    if parsed.scheme == 'rediss':
        kwargs['ssl_cert_reqs'] = None
    
    return redis_sync.Redis.from_url(clean_url, **kwargs)


def get_async_redis() -> redis.Redis:
    """
    Crée un client Redis asynchrone avec SSL correctement configuré.
    
    Écrase ssl_cert_reqs de l'URL pour éviter l'erreur avec redis-py asyncio.
    Utilise resolve_redis_url() pour garantir la cohérence avec les workers Celery.
    """
    from app.core.config import resolve_redis_url
    import logging
    import os

    logger = logging.getLogger(__name__)

    # S'assurer que redis.asyncio expose bien redis.constants pour éviter l'AttributeError
    _ensure_asyncio_constants()
    
    # Log les variables d'environnement pour diagnostic
    celery_broker = os.getenv('CELERY_BROKER_URL', 'NOT_SET')
    redis_url_env = os.getenv('REDIS_URL', 'NOT_SET')
    logger.info(f"🔍 [GET_ASYNC_REDIS] CELERY_BROKER_URL: {'SET' if celery_broker != 'NOT_SET' else 'NOT_SET'}")
    logger.info(f"🔍 [GET_ASYNC_REDIS] REDIS_URL: {'SET' if redis_url_env != 'NOT_SET' else 'NOT_SET'}")
    
    redis_url = resolve_redis_url()
    
    # Log l'URL Redis utilisée (masquer le mot de passe)
    masked_url = redis_url.split('@')[0] + '@***' if '@' in redis_url else redis_url
    logger.info(f"🔧 [GET_ASYNC_REDIS] Creating Redis client with URL: {masked_url}")
    
    # Parser l'URL et retirer ssl_cert_reqs de la query string
    parsed = urlparse(redis_url)
    query_params = parse_qs(parsed.query)
    
    # Log la base de données utilisée
    db_num = parsed.path.lstrip('/') if parsed.path else '0'
    logger.info(f"🔧 [GET_ASYNC_REDIS] Redis database number: {db_num}")
    
    # Retirer ssl_cert_reqs de la query string pour éviter le conflit
    if 'ssl_cert_reqs' in query_params:
        del query_params['ssl_cert_reqs']
    
    # Reconstruire l'URL sans ssl_cert_reqs
    new_query = urlencode(query_params, doseq=True)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
    # Pour les URLs non-SSL (redis://), ne pas passer ssl_cert_reqs
    # Pour les URLs SSL (rediss://), passer ssl_cert_reqs=None
    kwargs = {
        'decode_responses': True,
        'max_connections': 1,
    }
    
    if parsed.scheme == 'rediss':
        kwargs['ssl_cert_reqs'] = None
    
    client = redis.Redis.from_url(clean_url, **kwargs)
    
    logger.info(f"✅ [GET_ASYNC_REDIS] Redis client created successfully")
    return client
