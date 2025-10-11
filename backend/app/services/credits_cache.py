import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from app.core.redis_client import get_redis_client, RedisClient
from app.services.credits_service import CreditsService

logger = logging.getLogger(__name__)


class ConcurrencyError(Exception):
    """Exception levée lorsqu'une opération concurrente est détectée."""
    pass


class CreditsCacheService:
    """
    Cache service for credits and subscriptions using Redis.

    Patterns used:
    - Cache-aside for reads (balance, plans)
    - Write-through for writes (deductions)
    - Rate limiting by user

    Redis keys:
    - credits:balance:{user_id} (TTL: 60s)
    - credits:batch:{user_id}:{conversation_id} (TTL: 300s)
    - credits:ratelimit:{user_id} (TTL: 60s)
    - credits:lock:{user_id} (TTL: 5s)
    - credits:plans (TTL: 3600s)
    - credits:models (TTL: 3600s)
    """

    def __init__(self, redis_client: RedisClient, credits_service: CreditsService):
        self.redis = redis_client
        self.credits_service = credits_service

        self.BALANCE_TTL = 60          
        self.BATCH_TTL = 300          
        self.RATE_LIMIT_TTL = 60   
        self.LOCK_TTL = 5           
        self.PLANS_TTL = 3600     
        self.MODELS_TTL = 3600        


        self.RATE_LIMIT_REQUESTS = 100  


    async def get_balance(self, user_id: str) -> Optional[int]:
        """
        Get the credit balance from the cache or the DB.

        Pattern: Cache-aside
        """
        cache_key = f"credits:balance:{user_id}"

        try:
            cached_balance = await self.redis.get(cache_key)
            if cached_balance is not None:
                logger.debug(f"✅ Cache hit balance: {user_id} = {cached_balance}")
                return int(cached_balance)

            logger.debug(f"❌ Cache miss balance: {user_id}")
            balance = await self._fetch_balance_from_db(user_id)

            if balance is not None:
                await self.redis.setex(cache_key, self.BALANCE_TTL, str(balance))
                logger.debug(f"💾 Balance cached: {user_id} = {balance}")

            return balance

        except Exception as e:
            logger.error(f"Error fetching balance {user_id}: {e}")
            return await self._fetch_balance_from_db(user_id)

    async def invalidate_balance(self, user_id: str) -> bool:
        """Invalidate the cache of the credit balance."""
        cache_key = f"credits:balance:{user_id}"
        try:
            result = await self.redis.delete(cache_key)
            if result > 0:
                logger.debug(f"🗑️ Balan ce cache invalidated: {user_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Error invalidating cache balance {user_id}: {e}")
            return False

    async def _fetch_balance_from_db(self, user_id: str) -> Optional[int]:
        """Get the balance from the DB."""
        try:
            balance_data = await self.credits_service.get_credits_balance(user_id)
            return balance_data.balance
        except Exception as e:
            logger.error(f"Error fetching balance from DB {user_id}: {e}")
            return None


    async def get_batch_counter(self, user_id: str, conversation_id: str) -> int:
        """Get the batch counter for this batch."""
        cache_key = f"credits:batch:{user_id}:{conversation_id}"

        try:
            counter = await self.redis.get(cache_key)
            return int(counter) if counter else 0
        except Exception as e:
            logger.error(f"Error fetching batch counter {user_id}:{conversation_id}: {e}")
            return 0

    async def increment_batch_counter(self, user_id: str, conversation_id: str) -> int:
        """Increment and return the batch counter."""
        cache_key = f"credits:batch:{user_id}:{conversation_id}"

        try:
            async with self.redis.pipeline_context() as pipe:
                pipe.incr(cache_key)
                pipe.expire(cache_key, self.BATCH_TTL)
                results = await pipe.execute()

            new_count = results[0]
            logger.debug(f"📈 Batch counter: {user_id}:{conversation_id} = {new_count}")
            return new_count

        except Exception as e:
            logger.error(f"Error incrementing batch counter {user_id}:{conversation_id}: {e}")
            return 0

    async def reset_batch_counter(self, user_id: str, conversation_id: str) -> bool:
        """Reset the batch counter."""
        cache_key = f"credits:batch:{user_id}:{conversation_id}"

        try:
            result = await self.redis.delete(cache_key)
            if result > 0:
                logger.debug(f"🔄 Batch counter reset: {user_id}:{conversation_id}")
            return result > 0
        except Exception as e:
            logger.error(f"Erreur reset batch counter {user_id}:{conversation_id}: {e}")
            return False



    async def acquire_lock(self, user_id: str, lock_value: str, ttl: int = None) -> bool:
        """
        Acquire a distributed lock for the user.

        Args:
            user_id: User ID
            lock_value: Unique lock value (UUID)
            ttl: TTL of the lock in seconds (default: LOCK_TTL)

        Returns:
            bool: True if lock acquired, False otherwise
        """
        if ttl is None:
            ttl = self.LOCK_TTL

        lock_key = f"credits:lock:{user_id}"

        try:
            acquired = await self.redis.set(lock_key, lock_value, nx=True, ex=ttl)
            if acquired:
                logger.debug(f"🔒 Lock acquired: {user_id}")
            else:
                logger.debug(f"❌ Lock already held: {user_id}")
            return acquired
        except Exception as e:
            logger.error(f"Error acquiring lock {user_id}: {e}")
            return False

    async def release_lock(self, user_id: str, lock_value: str) -> bool:
        """
        Release a distributed lock with property verification.

        Uses a Lua script to avoid race conditions.
        """
        lock_key = f"credits:lock:{user_id}"

        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await self.redis.eval(script, [lock_key], [lock_value])
            if result > 0:
                logger.debug(f"🔓 Lock released: {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Lock release failed - not owner: {user_id}")
                return False
        except Exception as e:
            logger.error(f"Error releasing lock {user_id}: {e}")
            return False

    async def deduct_with_lock(self, user_id: str, amount: float, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Deduct credits with distributed lock to avoid race conditions.

        Returns:
            Dict with 'success', 'transaction', 'error'
        """
        lock_value = f"deduct-{user_id}-{asyncio.get_event_loop().time()}"
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                lock_acquired = await self.acquire_lock(user_id, lock_value, ttl=5)
                if not lock_acquired:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (2 ** attempt)) 
                        continue
                    else:
                        raise ConcurrencyError("Impossible to acquire the lock")

    
                try:
                    transaction = await self.credits_service.deduct_credits(
                        user_id=user_id,
                        credits_to_deduct=amount,
                        reason="AI call with Redis lock",
                        metadata=metadata
                    )

                    
                    await self.invalidate_balance(user_id)

                    return {
                        'success': True,
                        'transaction': transaction,
                        'error': None
                    }

                finally:
                    await self.release_lock(user_id, lock_value)

            except ConcurrencyError:
                logger.warning(f"Race condition detected for {user_id}, attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'transaction': None,
                        'error': 'concurrency_conflict'
                    }
            except Exception as e:
                logger.error(f"Error deducting with lock {user_id}: {e}")
                return {
                    'success': False,
                    'transaction': None,
                    'error': str(e)
                }

    async def check_rate_limit(self, user_id: str, limit: int = None) -> Dict[str, Any]:
        """
        Check and update the rate limiting for the user.

        Returns:
            Dict with 'allowed', 'current_count', 'reset_in_seconds'
        """
        if limit is None:
            limit = self.RATE_LIMIT_REQUESTS

        rate_key = f"credits:ratelimit:{user_id}"

        try:
            async with self.redis.pipeline_context() as pipe:
                pipe.incr(rate_key)
                pipe.expire(rate_key, self.RATE_LIMIT_TTL)
                results = await pipe.execute()

            current_count = results[0]

            if current_count > limit:
                
                reset_ttl = await self.redis.ttl(rate_key)
                logger.warning(f"🚫 Rate limit exceeded: {user_id} ({current_count}/{limit})")
                return {
                    'allowed': False,
                    'current_count': current_count,
                    'reset_in_seconds': reset_ttl,
                    'limit': limit
                }
            else:
                logger.debug(f"✅ Rate limit OK: {user_id} ({current_count}/{limit})")
                return {
                    'allowed': True,
                    'current_count': current_count,
                    'reset_in_seconds': self.RATE_LIMIT_TTL,
                    'limit': limit
                }

        except Exception as e:
            logger.error(f"Erreur rate limiting {user_id}: {e}")
            
            return {
                'allowed': True,
                'current_count': 0,
                'reset_in_seconds': self.RATE_LIMIT_TTL,
                'limit': limit,
                'error': str(e)
            }


    async def get_cached_plans(self) -> Optional[List[Dict[str, Any]]]:
        """Get the subscription plans from the cache."""
        cache_key = "credits:plans"

        try:
            cached_plans = await self.redis.get(cache_key)
            if cached_plans:
                return json.loads(cached_plans)

            # Cache miss - to implement with DB fetch
            return None

        except Exception as e:
            logger.error(f"Erreur récupération plans cachés: {e}")
            return None

    async def cache_plans(self, plans: List[Dict[str, Any]]) -> bool:
        """Met en cache les plans d'abonnement."""
        cache_key = "credits:plans"

        try:
            plans_json = json.dumps(plans)
            result = await self.redis.setex(cache_key, self.PLANS_TTL, plans_json)
            return result
        except Exception as e:
            logger.error(f"Erreur mise en cache plans: {e}")
            return False

    async def get_cached_models(self) -> Optional[List[Dict[str, Any]]]:
        """Get the AI models from the cache."""
        cache_key = "credits:models"

        try:
            cached_models = await self.redis.get(cache_key)
            if cached_models:
                return json.loads(cached_models)

            # Cache miss - to implement with DB fetch
            return None

        except Exception as e:
            logger.error(f"Erreur récupération modèles cachés: {e}")
            return None

    async def cache_models(self, models: List[Dict[str, Any]]) -> bool:
        """Cache the AI models."""
        cache_key = "credits:models"

        try:
            models_json = json.dumps(models)
            result = await self.redis.setex(cache_key, self.MODELS_TTL, models_json)
            return result
        except Exception as e:
            logger.error(f"Erreur mise en cache modèles: {e}")
            return False

    

    async def clear_user_cache(self, user_id: str) -> bool:
        """Clear all the cache for a user."""
        keys_pattern = f"credits:*:{user_id}*"

        try:
            # Use SCAN to find all the keys for the user
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=keys_pattern, count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)

                if cursor == 0:
                    break

            logger.info(f"🧹 Cache cleared for {user_id}: {deleted_count} keys deleted")
            return True

        except Exception as e:
            logger.error(f"Erreur nettoyage cache {user_id}: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le cache."""
        try:
            info = await self.redis.info()
            return {
                'redis_connected_clients': info.get('connected_clients', 0),
                'redis_used_memory': info.get('used_memory_human', 'unknown'),
                'redis_uptime_days': info.get('uptime_in_days', 0),
                'cache_healthy': await self.redis.health_check()
            }
        except Exception as e:
            logger.error(f"Erreur récupération stats cache: {e}")
            return {'error': str(e)}

    async def warmup_cache(self) -> Dict[str, Any]:
        """
        Précharge le cache avec les données fréquemment utilisées.

        À appeler au démarrage de l'application.
        """
        logger.info("🔥 Warming up credits cache...")

        results = {
            'plans_cached': False,
            'models_cached': False,
            'errors': []
        }

        try:
            # TODO: Implémenter le fetch depuis DB et mise en cache
            # Pour l'instant, juste vérifier la connexion
            health = await self.redis.health_check()
            results['redis_healthy'] = health

            if health:
                logger.info("✅ Credits cache warmup completed")
            else:
                logger.warning("⚠️ Credits cache warmup failed - Redis unavailable")

        except Exception as e:
            results['errors'].append(str(e))
            logger.error(f"Erreur warmup cache: {e}")

        return results



async def get_credits_cache_service(
    redis_client: RedisClient = None,
    credits_service: CreditsService = None
) -> CreditsCacheService:
    """Dépendance FastAPI pour injecter le service de cache des crédits."""
    if redis_client is None:
        redis_client = get_redis_client()
    if credits_service is None:
        from app.services.credits_service import get_credits_service
        credits_service = await get_credits_service()

    return CreditsCacheService(redis_client, credits_service)
