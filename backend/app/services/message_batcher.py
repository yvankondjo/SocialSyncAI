import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import redis.asyncio as redis
from contextlib import asynccontextmanager
import os

logger = logging.getLogger(__name__)

class MessageBatcher:
    """
    Service de batching pour messages WhatsApp/Instagram
    
    Logique:
    1. Messages sauvés immédiatement en BDD (idempotent)
    2. Messages ajoutés à Redis pour batching
    3. Fenêtre glissante de 30s (trailing debounce)
    4. Scanner traite les batches dus
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis_pool: Optional[redis.ConnectionPool] = None
        self.batch_window_seconds = 30
        self.cache_ttl_hours = 1
        self.history_limit = 200
        
    async def get_redis(self) -> redis.Redis:
        """Obtenir une connexion Redis du pool"""
        if not self._redis_pool:
            self._redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20
            )
        return redis.Redis(connection_pool=self._redis_pool)
    
    @asynccontextmanager
    async def redis_connection(self):
        """Context manager pour connexions Redis"""
        redis_client = await self.get_redis()
        try:
            yield redis_client
        finally:
            await redis_client.close()
    
    def _get_conversation_key(self, platform: str, account_id: str, contact_id: str) -> str:
        """Clé de base pour une conversation"""
        return f"conv:{platform}:{account_id}:{contact_id}"
    
    async def add_message_to_batch(
        self, 
        platform: str,
        account_id: str, 
        contact_id: str,
        message_data: Dict[str, Any],
        conversation_id: str = None
    ) -> bool:
        """
        Ajouter un message au batch Redis
        
        Args:
            platform: whatsapp, instagram
            account_id: phone_number_id ou instagram_business_account_id
            contact_id: wa_id ou ig_user_id
            message_data: Données complètes du message
            conversation_id: UUID de la conversation en BDD
            
        Returns:
            bool: True si premier message de la session, False sinon
        """
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        
        async with self.redis_connection() as redis_client:
            # Préparer les données à stocker
            batch_message = {
                "message_data": message_data,
                "conversation_id": conversation_id,
                "received_at": datetime.now().isoformat(),
                "platform": platform,
                "account_id": account_id,
                "contact_id": contact_id
            }
            
            # 1. Vérifier si conversation existe déjà (cache hit/miss)
            history_exists = await redis_client.exists(f"{base_key}:history")
            
            # 2. Si première fois ou cache expiré, charger depuis BDD
            if not history_exists:
                logger.info(f"Cache miss pour {base_key} - hydratation nécessaire")
                await self._hydrate_conversation_cache(
                    redis_client, base_key, platform, account_id, contact_id
                )
            
            # 3. Ajouter message à l'historique (borné)
            await redis_client.lpush(f"{base_key}:history", json.dumps(batch_message))
            await redis_client.ltrim(f"{base_key}:history", 0, self.history_limit - 1)
            await redis_client.expire(f"{base_key}:history", self.cache_ttl_hours * 3600)
            
            # 4. Ajouter message à la queue de batch
            await redis_client.rpush(f"{base_key}:msgs", json.dumps(batch_message))
            await redis_client.expire(f"{base_key}:msgs", self.cache_ttl_hours * 3600)
            
            # 5. Définir la deadline SEULEMENT si elle n'existe pas (timer fixe)
            conversation_identifier = f"{platform}:{account_id}:{contact_id}"
            existing_deadline = await redis_client.get(f"{base_key}:deadline")
            
            if not existing_deadline:
                # Premier message de la session → définir deadline fixe
                deadline = datetime.now() + timedelta(seconds=self.batch_window_seconds)
                deadline_timestamp = int(deadline.timestamp())
                
                await redis_client.set(
                    f"{base_key}:deadline", 
                    deadline_timestamp, 
                    ex=self.cache_ttl_hours * 3600
                )
                
                # Ajouter à l'agenda global (ZSET)
                await redis_client.zadd(
                    "conv:deadlines", 
                    {conversation_identifier: deadline_timestamp}
                )
                
                logger.info(f"⏰ Timer 30s démarré pour {base_key}, deadline: {deadline}")
            else:
                # Messages suivants → deadline INCHANGÉE
                existing_deadline_dt = datetime.fromtimestamp(int(existing_deadline))
                logger.info(f"📝 Message ajouté au batch {base_key}, deadline inchangée: {existing_deadline_dt}")
                # Pas de ZADD car déjà dans l'agenda
            
            return not history_exists
    
    async def _hydrate_conversation_cache(
        self,
        redis_client: redis.Redis,
        base_key: str,
        platform: str,
        account_id: str,
        contact_id: str
    ):
        """
        Charger l'historique depuis la BDD vers Redis (Supabase)
        """
        try:
            from app.db.session import get_db

            db = get_db()
            # Requête unique avec jointures imbriquées (inner) via PostgREST
            select_str = (
                "id, content, direction, message_type, external_message_id, created_at, "
                "conversations!inner(id, customer_identifier, "
                "social_accounts!inner(id, platform, account_id))"
            )
            msgs_res = (
                db.table("conversation_messages")
                .select(select_str)
                .eq("conversations.customer_identifier", contact_id)
                .eq("conversations.social_accounts.platform", platform)
                .eq("conversations.social_accounts.account_id", account_id)
                .order("created_at", desc=True)
                .limit(self.history_limit)
                .execute()
            )
            msgs = msgs_res.data or []

            if msgs:
                history_messages = []
                for row in reversed(msgs):  # plus ancien → plus récent
                    conv = row.get("conversations") or {}
                    conv_id = conv.get("id")
                    history_msg = {
                        "message_data": {
                            "id": str(row.get("id")),
                            "content": row.get("content"),
                            "direction": row.get("direction"),
                            "message_type": row.get("message_type"),
                            "external_message_id": row.get("external_message_id"),
                            "created_at": row.get("created_at"),
                        },
                        "conversation_id": str(conv_id) if conv_id else None,
                        "received_at": row.get("created_at"),
                        "platform": platform,
                        "account_id": account_id,
                        "contact_id": contact_id,
                    }
                    history_messages.append(json.dumps(history_msg))

                await redis_client.rpush(f"{base_key}:history", *history_messages)
                await redis_client.expire(f"{base_key}:history", self.cache_ttl_hours * 3600)
                logger.info(f"Cache hydraté pour {base_key}: {len(history_messages)} messages")

            await redis_client.hset(f"{base_key}:meta", mapping={
                "last_db_sync": datetime.now().isoformat(),
                "platform": platform,
                "account_id": account_id,
                "contact_id": contact_id,
            })
            await redis_client.expire(f"{base_key}:meta", self.cache_ttl_hours * 3600)

        except Exception as e:
            logger.error(f"Erreur lors de l'hydratation du cache {base_key}: {e}")
            # Continue quand même, juste sans historique
    
    async def get_due_conversations(self) -> List[Dict[str, Any]]:
        """
        Récupérer les conversations dont la deadline est échue
        """
        async with self.redis_connection() as redis_client:
            now_timestamp = int(datetime.now().timestamp())
            
            # Récupérer conversations dues (score ≤ maintenant)
            due_conversations = await redis_client.zrangebyscore(
                "conv:deadlines", 
                0, 
                now_timestamp,
                withscores=True
            )
            
            result = []
            for conv_id, deadline_score in due_conversations:
                # Parse conversation ID
                try:
                    platform, account_id, contact_id = conv_id.split(":", 2)
                    result.append({
                        "platform": platform,
                        "account_id": account_id,
                        "contact_id": contact_id,
                        "deadline": deadline_score,
                        "conversation_key": self._get_conversation_key(platform, account_id, contact_id)
                    })
                except ValueError:
                    logger.warning(f"Format de conversation invalide: {conv_id}")
                    continue
            
            return result
    
    async def process_batch_for_conversation(
        self, 
        platform: str, 
        account_id: str, 
        contact_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Traiter le batch d'une conversation donnée
        
        Returns:
            Dict avec les messages traités ou None si déjà traité
        """
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        conversation_identifier = f"{platform}:{account_id}:{contact_id}"
        
        async with self.redis_connection() as redis_client:
            # 1. Prendre un lock distribué
            lock_key = f"{base_key}:lock"
            lock_acquired = await redis_client.set(
                lock_key, 
                "processing", 
                nx=True, 
                ex=20  # Lock expire après 20s
            )
            
            if not lock_acquired:
                logger.info(f"Batch {base_key} déjà en cours de traitement")
                return None
            
            try:
                # 2. Vérifier que la deadline est bien échue (sécurité)
                current_deadline = await redis_client.get(f"{base_key}:deadline")
                if current_deadline and int(current_deadline) > datetime.now().timestamp():
                    logger.warning(f"Deadline pas encore échue pour {base_key}, abandon (race condition)")
                    return None
                
                # 3. Récupérer et vider la queue des messages
                messages_raw = await redis_client.lrange(f"{base_key}:msgs", 0, -1)
                if not messages_raw:
                    logger.info(f"Aucun message en attente pour {base_key}")
                    return None
                
                await redis_client.delete(f"{base_key}:msgs")
                
                # 4. Parser les messages
                messages = []
                for msg_raw in messages_raw:
                    try:
                        messages.append(json.loads(msg_raw))
                    except json.JSONDecodeError:
                        logger.warning(f"Message invalide ignoré: {msg_raw}")
                
                # 5. Récupérer contexte récent pour IA
                context_raw = await redis_client.lrange(f"{base_key}:history", -40, -1)
                context_messages = []
                for ctx_raw in context_raw:
                    try:
                        context_messages.append(json.loads(ctx_raw))
                    except json.JSONDecodeError:
                        continue
                
                # 6. Nettoyer l'agenda global
                await redis_client.zrem("conv:deadlines", conversation_identifier)
                await redis_client.delete(f"{base_key}:deadline")
                
                logger.info(f"Batch traité pour {base_key}: {len(messages)} messages")
                
                # Déduire la conversation_id si présente
                conversation_id = None
                print(messages)
                if messages and isinstance(messages[0], dict):
                    print(messages[0])
                    conversation_id = messages[0].get("conversation_id")
                
                return {
                    "platform": platform,
                    "account_id": account_id,
                    "contact_id": contact_id,
                    "messages": messages,
                    "context": context_messages,
                    "conversation_key": base_key,
                    "conversation_id": conversation_id
                }
                
            finally:
                # 7. Libérer le lock
                await redis_client.delete(lock_key)
    
    async def add_response_to_history(
        self,
        platform: str,
        account_id: str,
        contact_id: str,
        response_data: Dict[str, Any]
    ):
        """
        Ajouter la réponse envoyée à l'historique Redis
        """
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        
        response_message = {
            "message_data": response_data,
            "received_at": datetime.now().isoformat(),
            "platform": platform,
            "account_id": account_id,
            "contact_id": contact_id,
            "direction": "outbound"
        }
        
        async with self.redis_connection() as redis_client:
            await redis_client.lpush(f"{base_key}:history", json.dumps(response_message))
            await redis_client.ltrim(f"{base_key}:history", 0, self.history_limit - 1)
            await redis_client.expire(f"{base_key}:history", self.cache_ttl_hours * 3600)
    
    async def cleanup_expired_data(self):
        """
        Nettoyer les données expirées (optionnel, Redis TTL s'en charge)
        """
        async with self.redis_connection() as redis_client:
            # Nettoyer les deadlines expirées
            expired_threshold = int(datetime.now().timestamp()) - (self.cache_ttl_hours * 3600)
            removed = await redis_client.zremrangebyscore("conv:deadlines", 0, expired_threshold)
            if removed:
                logger.info(f"Nettoyage: {removed} deadlines expirées supprimées")
    
    async def close(self):
        """Fermer les connexions Redis"""
        if self._redis_pool:
            await self._redis_pool.disconnect()

message_batcher = MessageBatcher()
