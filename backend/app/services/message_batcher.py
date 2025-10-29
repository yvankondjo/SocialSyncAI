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
    Service of batching for WhatsApp/Instagram messages
    
    Logique simplifiée:
    1. Messages sauvegardés immédiatement en BDD
    2. Messages ajoutés à Redis pour groupement
    3. Fenêtre glissante de 15s (debounce)
    4. Scanner traite les batches dus
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_pools = {}  # Store pools per event loop
        self.batch_window_seconds = 2
        self.cache_ttl_hours = 0.5

    async def get_redis(self) -> redis.Redis:
        """
        Get a Redis connection from a pool tied to the current event loop.

        Creates a separate connection pool for each event loop to avoid
        "Event loop is closed" errors in Celery workers.
        """
        try:
            logger.debug("[DEBUG] get_redis: Getting running loop...")
            # Get the current running loop
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
            logger.debug(f"[DEBUG] get_redis: Loop ID = {loop_id}, is_closed = {loop.is_closed()}")

            # Create a pool for this loop if it doesn't exist
            if loop_id not in self._redis_pools:
                logger.info(f"[DEBUG] Creating new Redis connection pool for event loop {loop_id}")
                self._redis_pools[loop_id] = redis.ConnectionPool.from_url(
                    self.redis_url,
                    decode_responses=True,
                    max_connections=20
                )
            else:
                logger.debug(f"[DEBUG] get_redis: Reusing existing pool for loop {loop_id}")

            logger.debug(f"[DEBUG] get_redis: Creating Redis client from pool...")
            client = redis.Redis(connection_pool=self._redis_pools[loop_id])
            logger.debug(f"[DEBUG] get_redis: Redis client created successfully")
            return client
        except RuntimeError as e:
            # No running loop - create a direct connection (fallback)
            logger.error(f"[DEBUG] get_redis: RuntimeError - {e}")
            logger.warning("No running event loop, creating direct Redis connection")
            return redis.Redis.from_url(self.redis_url, decode_responses=True)

    @asynccontextmanager
    async def redis_connection(self):
        """
        Context manager for Redis connections.

        Note: We DON'T close the client here because it uses a shared ConnectionPool.
        Closing it would interfere with the pool's lifecycle and cause "Event loop is closed" errors
        in async workers. The pool manages connections automatically.
        """
        redis_client = await self.get_redis()
        yield redis_client
        # Don't close - the connection pool is reused across calls

    def _get_conversation_key(self, platform: str, account_id: str, contact_id: str) -> str:
        """Base key for a conversation"""
        return f'conv:{platform}:{account_id}:{contact_id}'

    async def add_message_to_batch(self, platform: str, account_id: str, contact_id: str, message_data: Dict[str, Any], conversation_message_id: str) -> bool:
        """
        Add a message to the Redis batch

        Args:
            platform: whatsapp, instagram
            account_id: phone_number_id or instagram_business_account_id
            contact_id: wa_id or ig_user_id
            message_data: Full message data
            conversation_message_id: UUID of the message in the DB

        Returns:
            bool: True if first message of the session, False otherwise
        """
        # Initialiser les variables pour éviter les erreurs de portée
        conversation_identifier = f'{platform}:{account_id}:{contact_id}'
        deadline_timestamp = None
        
        try:
            if not conversation_message_id:
                logger.error('conversation_message_id cannot be None or empty')
                return False

            if not message_data:
                logger.error('message_data cannot be None')
                return False

            base_key = self._get_conversation_key(platform, account_id, contact_id)
            async with self.redis_connection() as redis_client:
                batch_message = {
                    'message_data': message_data["metadata"],
                    'conversation_message_id': conversation_message_id,
                    'message_type': message_data["message_type"],
                    'external_message_id': message_data["external_message_id"]
                }

                try:
                    await redis_client.rpush(f'{base_key}:msgs', json.dumps(batch_message))
                    await redis_client.expire(f'{base_key}:msgs', int(self.cache_ttl_hours * 3600))

                    existing_deadline = await redis_client.get(f'{base_key}:deadline')

                    if not existing_deadline:
                        deadline = datetime.now() + timedelta(seconds=self.batch_window_seconds)
                        deadline_timestamp = int(deadline.timestamp())
                        
                        
                        await redis_client.set(f'{base_key}:deadline', deadline_timestamp, ex=int(self.cache_ttl_hours * 3600))
                        
                        await redis_client.zadd('conv:deadlines', {conversation_identifier: deadline_timestamp})
                        
                        await redis_client.set(f'{base_key}:conversation_id', message_data["conversation_id"], ex=int(self.cache_ttl_hours * 3600))
                        logger.info(f'⏰ Timer 15s started for {base_key}, deadline: {deadline}')
                        return True
                    else:
                        existing_deadline_dt = datetime.fromtimestamp(int(existing_deadline))
                        logger.info(f'📝 Message added to batch {base_key}, deadline unchanged: {existing_deadline_dt}')
                        return False

                except Exception as redis_error:
                    logger.error(f'Redis operation failed for {base_key}: {redis_error}')
                    return False

        except Exception as e:
            logger.error(f'Error adding message to batch: {e}')
            return False


    async def get_due_conversations(self) -> List[Dict[str, Any]]:
        """
        Get the conversations whose deadline has expired
        """
        logger.debug("[DEBUG] get_due_conversations: Starting...")
        try:
            logger.debug("[DEBUG] get_due_conversations: Entering redis_connection context...")
            async with self.redis_connection() as redis_client:
                logger.debug("[DEBUG] get_due_conversations: Got redis_client, querying deadlines...")
                now_timestamp = int(datetime.now().timestamp())
                due_conversations = await redis_client.zrangebyscore('conv:deadlines', 0, now_timestamp, withscores=True)
                logger.debug(f"[DEBUG] get_due_conversations: Found {len(due_conversations)} due conversations")
                if due_conversations:
                    logger.info(f'Found {len(due_conversations)} due conversations: {[conv[0] for conv in due_conversations]}')
                result = []
                for conv_id, deadline_score in due_conversations:
                    try:
                        platform, account_id, contact_id = conv_id.split(':', 2)
                        base_key = self._get_conversation_key(platform, account_id, contact_id)
                        conversation_id = await redis_client.get(f'{base_key}:conversation_id')
                        result.append({'platform': platform, 'account_id': account_id, 'contact_id': contact_id, 'deadline': deadline_score, 'conversation_key': base_key, 'conversation_id': conversation_id})
                    except ValueError:
                        logger.warning(f'Invalid conversation format: {conv_id}')
                logger.debug(f"[DEBUG] get_due_conversations: Returning {len(result)} results")
                return result
        except Exception as e:
            logger.error(f"[DEBUG] get_due_conversations: Exception - {type(e).__name__}: {e}", exc_info=True)
            raise

    async def process_batch_for_conversation(self, platform: str, account_id: str, contact_id: str, conversation_key: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Process the batch for a given conversation
        
        Returns:
            Dict with the processed messages or None if already processed
        """
        base_key = conversation_key
        conversation_identifier = f'{platform}:{account_id}:{contact_id}'
        async with self.redis_connection() as redis_client:
            lock_key = f'{base_key}:lock'
            lock_acquired = await redis_client.set(lock_key, 'processing', nx=True, ex=20)
            if not lock_acquired:
                logger.info(f'Batch {base_key} already being processed')
                return None
            
            try:
                current_deadline = await redis_client.get(f"{base_key}:deadline")
                if current_deadline and int(current_deadline) > datetime.now().timestamp():
                    logger.warning(f"Deadline pas encore atteinte pour {base_key}, abandon (race condition)")
                    return None
                
                # Récupérer les messages du batch
                messages_raw = await redis_client.lrange(f"{base_key}:msgs", 0, -1)
                if not messages_raw:    
                    logger.info(f"No message in waiting for {base_key}")
                    return None

                # Nettoyer le batch
                await redis_client.delete(f"{base_key}:msgs")
                await redis_client.zrem("conv:deadlines", conversation_identifier)
                await redis_client.delete(f"{base_key}:deadline")

                context_messages_text_only = ""
                context_messages =[]
                message_ids = []
                last_external_message_id = None
                #check if there is only one image in the messages
                image_in_messages = False
                storage_object_name_list = []
                for msg_raw in messages_raw:
                    msg_data = json.loads(msg_raw)
                    if msg_data.get("message_type") == "image":
                        image_in_messages = True
                        continue
                for msg_raw in messages_raw:
                    try:
                        msg_data = json.loads(msg_raw)
                        # Le contenu est directement dans message_data car on a stocké metadata comme message_data
                        content = msg_data.get("message_data", {}).get("content", "")
                        logger.info(f"🔍 DEBUG message_batcher - msg_data: {msg_data}")
                        logger.info(f"🔍 DEBUG message_batcher - content extracted: '{content}'")
                        if image_in_messages:
                            if msg_data.get("message_type") == "image":
                                storage_object_name_list.append(msg_data.get("message_data", {}).get("storage_object_name"))
                                
                                if isinstance(content, list):
                                    context_messages.extend(content)
                                else:
                                    context_messages.append(content)
                            elif msg_data.get("message_type") == "text":
                               
                                context_messages.append({"type": "text", "text": content})
                            else:
                                continue
                        else:
                            context_messages_text_only = context_messages_text_only + " " + content
                            
                        external_id = msg_data.get("external_message_id", "")
                        message_ids.append(external_id)
                        last_external_message_id = external_id
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"Invalid message ignored: {msg_raw} - Error: {e}")
                
                messages = {
                "message_data": {"role": "user", "content": context_messages_text_only if not image_in_messages else context_messages},
                "storage_object_name_list": storage_object_name_list,
                "external_message_id": last_external_message_id
            }
                     

                logger.info(f"Batch processed for {base_key}: 1 concatenated message")
                
                
                print(f"Messages structure: {type(messages)}")
                print(f"Messages content: {messages}")
                if messages and isinstance(messages, dict):
                    print(f"Message data: {messages.get('message_data', {})}")
                
                return {
                    "platform": platform,
                    "account_id": account_id,
                    "contact_id": contact_id,
                    "messages": messages,
                    "message_ids": message_ids,
                    "conversation_key": base_key,
                    "conversation_id": conversation_id
                }
                
            finally:
                
                await redis_client.delete(lock_key)
    
    async def cleanup_expired_data(self):
        """
        Clean expired data (optional, Redis TTL handles it)
        """
        async with self.redis_connection() as redis_client:
            expired_threshold = int(datetime.now().timestamp()) - self.cache_ttl_hours * 3600
            removed = await redis_client.zremrangebyscore('conv:deadlines', 0, expired_threshold)
            if removed:
                logger.info(f'Cleaning: {removed} expired deadlines removed')

    async def close(self):
        """Close the Redis connections"""
        if self._redis_pool:
            await self._redis_pool.disconnect()

    async def delete_conversation_cache(self, platform: str, account_id: str, contact_id: str):
        """Delete the conversation cache"""
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        conversation_identifier = f'{platform}:{account_id}:{contact_id}'
        async with self.redis_connection() as redis_client:
            await redis_client.delete(f'{base_key}:msgs')
            await redis_client.delete(f'{base_key}:deadline')
            await redis_client.delete(f'{base_key}:conversation_id')
            await redis_client.delete(f'{base_key}:lock')
            await redis_client.zrem('conv:deadlines', conversation_identifier)


message_batcher = MessageBatcher()