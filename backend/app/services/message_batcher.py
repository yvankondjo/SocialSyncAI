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
    
    Logique:
    1. Messages saved immediately in DB (idempotent)
    2. Messages added to Redis for batching
    3. Sliding window of 15s (trailing debounce)
    4. Scanner processes due batches
    """

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_pool = None
        self.batch_window_seconds = 15
        self.cache_ttl_hours = 1
        self.history_limit = 200

    async def get_redis(self) -> redis.Redis:
        """Get a Redis connection from the pool"""
        if not self._redis_pool:
            self._redis_pool = redis.ConnectionPool.from_url(self.redis_url, decode_responses=True, max_connections=20)
        return redis.Redis(connection_pool=self._redis_pool)

    @asynccontextmanager
    async def redis_connection(self):
        """Context manager for Redis connections"""
        redis_client = await self.get_redis()
        try:
            yield redis_client
        finally:
            await redis_client.close()

    def _get_conversation_key(self, platform: str, account_id: str, contact_id: str) -> str:
        """Base key for a conversation"""
        return f'conv:{platform}:{account_id}:{contact_id}'

    async def add_message_to_batch(self, platform: str, account_id: str, contact_id: str, message_data: Dict[str, Any], conversation_message_id: str) -> bool:
        """
        Add a message to the Redis batch
        
        Args:
            platform: whatsapp, instagram
            account_id: phone_number_id ou instagram_business_account_id
            contact_id: wa_id ou ig_user_id
            message_data: Données complètes du message
            conversation_message_id: UUID du message en BDD
            
        Returns:
            bool: True si premier message de la session, False sinon
        """
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        async with self.redis_connection() as redis_client:
            conversation_id = message_data["conversation_id"]
            batch_message = {'message_data': message_data["metadata"], 'conversation_message_id': conversation_message_id, 'message_type': message_data["message_type"],"external_message_id": message_data["external_message_id"]}
            history_exists = await redis_client.exists(f'{base_key}:history')
            if not history_exists:
                logger.info(f'Cache miss pour {base_key} - hydratation nécessaire')
                await self._hydrate_conversation_cache(redis_client, base_key, platform, account_id, contact_id, conversation_id)
            
            try:
                await redis_client.ltrim(f'{base_key}:history', 0, self.history_limit - 1)
                await redis_client.expire(f'{base_key}:history', self.cache_ttl_hours * 3600)
                await redis_client.rpush(f'{base_key}:msgs', json.dumps(batch_message))
                await redis_client.expire(f'{base_key}:msgs', self.cache_ttl_hours * 3600)
                conversation_identifier = f'{platform}:{account_id}:{contact_id}'
                existing_deadline = await redis_client.get(f'{base_key}:deadline')
                if not existing_deadline:
                    deadline = datetime.now() + timedelta(seconds=self.batch_window_seconds)
                    deadline_timestamp = int(deadline.timestamp())
                    await redis_client.set(f'{base_key}:deadline', deadline_timestamp, ex=self.cache_ttl_hours * 3600)
                    await redis_client.zadd('conv:deadlines', {conversation_identifier: deadline_timestamp})
                    logger.info(f'⏰ Timer 15s démarré pour {base_key}, deadline: {deadline}')
                else:
                    existing_deadline_dt = datetime.fromtimestamp(int(existing_deadline))
                    logger.info(f'📝 Message ajouté au batch {base_key}, deadline inchangée: {existing_deadline_dt}')
                return not history_exists
            except Exception as e:
                logger.error(f'Error adding message to batch: {e}')
                return False

    async def _hydrate_conversation_cache(self, redis_client: redis.Redis, base_key: str, platform: str, account_id: str, contact_id: str, conversation_id: str):
        """
        Load the history from the DB to Redis (Supabase)
        """
        try:
            from app.db.session import get_db
            db = get_db()
            select_str = 'id, messages'
            msgs_res = db.table('conversations_message_groups').select(select_str).eq('conversation_id', conversation_id).order('created_at', desc=True).limit(self.history_limit).execute()
            msgs = msgs_res.data or []
            if msgs:
                history_messages = []
                for row in reversed(msgs):
                    messages = row.get('messages', {})
                    if isinstance(messages, dict):
                        if isinstance(messages.get('message_data').get("content"), list):
                            from app.services.response_manager import refresh_image_urls_in_message
                            messages= refresh_image_urls_in_message(messages)
                        history_messages.append({'message_data': messages['message_data'], 'conversation_id': conversation_id})
                    else:
                        logger.warning(f"Invalid messages format for message {row.get('id')}: {messages}")
                if history_messages:
                    for msg in history_messages:
                        try:
                            await redis_client.rpush(f'{base_key}:history', json.dumps(msg))
                        except Exception as e:
                            logger.error(f'Error serializing message for cache: {e}')
                    await redis_client.expire(f'{base_key}:history', self.cache_ttl_hours * 3600)
                    logger.info(f'Cache hydraté pour {base_key}: {len(history_messages)} messages')
            await redis_client.hset(f'{base_key}:meta', mapping={'last_db_sync': datetime.now().isoformat(), 'platform': platform, 'account_id': account_id, 'contact_id': contact_id})
            await redis_client.set(f'{base_key}:conversation_id', conversation_id, ex=self.cache_ttl_hours * 3600)
        except Exception as e:
            logger.error(f'Error hydrating cache {base_key}: {e}')

    async def get_due_conversations(self) -> List[Dict[str, Any]]:
        """
        Get the conversations whose deadline has expired
        """
        async with self.redis_connection() as redis_client:
            now_timestamp = int(datetime.now().timestamp())
            due_conversations = await redis_client.zrangebyscore('conv:deadlines', 0, now_timestamp, withscores=True)
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
            return result

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
                    logger.warning(f"Deadline not yet reached for {base_key}, abandon (race condition)")
                    return None
                
                
                messages_raw = await redis_client.lrange(f"{base_key}:msgs", 0, -1)
                if not messages_raw:    
                    logger.info(f"No message pending for {base_key}")
                    return None

                await redis_client.delete(f"{base_key}:msgs")
                
                await redis_client.zrem("conv:deadlines", conversation_identifier)
                await redis_client.delete(f"{base_key}:deadline")

                context_messages_text_only = ""
                context_messages =[]
                message_ids = []
                last_external_message_id = None
                #verifie si il y'a ne serait que une seule image parmir les message
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
                        content = msg_data.get("metadata", {}).get("content", "")
                        if image_in_messages:
                            if msg_data.get("message_type") == "image":
                                storage_object_name_list.append(msg_data.get("metadata", {}).get("storage_object_name"))
                                
                                if isinstance(content, list):
                                    context_messages.extend(content)
                                else:
                                    context_messages.append(content)
                                continue
                            elif msg_data.get("message_type") == "text":
                               
                                context_messages.append({"type": "text", "text": content})
                                continue
                            else:
                                continue
                        else:
                            context_messages_text_only = context_messages_text_only + " " + content
                            
                        message_ids.append(msg_data.get("message_id", ""))
                        last_external_message_id = msg_data.get("external_message_id")
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.warning(f"Invalid message ignored: {msg_raw} - Error: {e}")
                
                
               
               
                try:
                    messages = {
                    "message_data": {"role": "user", "content": context_messages_text_only if not image_in_messages else context_messages},
                    "storage_object_name_list": storage_object_name_list,
                    "external_message_id": last_external_message_id
                }
                    await redis_client.lpush(f"{base_key}:history", json.dumps( messages))
                except Exception as e:
                    logger.warning(f"Error adding message to history: {e}") 
                await redis_client.ltrim(f"{base_key}:history", 0, self.history_limit - 1)
                await redis_client.expire(f"{base_key}:history", self.cache_ttl_hours * 3600)
                
                
                context_raw = await redis_client.lrange(f"{base_key}:history", 0, -1)
                context_messages = []
                for ctx_raw in context_raw:
                    try:
                        context_messages.append(json.loads(ctx_raw))
                    except json.JSONDecodeError:
                        continue
                
                
                
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
                    "context": context_messages,
                    "conversation_key": base_key,
                    "conversation_id": conversation_id
                }
                
            finally:
                
                await redis_client.delete(lock_key)
    
    async def add_response_to_history(
        self,
        platform: str,
        account_id: str,
        contact_id: str,
        response_data: Dict[str, Any],
        conversation_id: str
    ):
        """
        Add the sent response to the Redis history
        """
        base_key = self._get_conversation_key(platform, account_id, contact_id)
        response_message = {'message_data': response_data, 'conversation_id': conversation_id}
        async with self.redis_connection() as redis_client:
            await redis_client.lpush(f'{base_key}:history', json.dumps(response_message))
            await redis_client.ltrim(f'{base_key}:history', 0, self.history_limit - 1)
            await redis_client.expire(f'{base_key}:history', self.cache_ttl_hours * 3600)

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
            await redis_client.delete(f'{base_key}:history')
            await redis_client.delete(f'{base_key}:msgs')
            await redis_client.delete(f'{base_key}:deadline')
            await redis_client.delete(f'{base_key}:meta')
            await redis_client.delete(f'{base_key}:lock')
            await redis_client.zrem('conv:deadlines', conversation_identifier)


message_batcher = MessageBatcher()