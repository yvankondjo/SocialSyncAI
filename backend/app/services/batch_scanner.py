import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from app.services.message_batcher import message_batcher
from app.services.response_manager import (
    generate_smart_response,
    get_user_credentials_by_platform_account,
    send_response,
    save_response_to_db,
    send_typing_indicator,
)
from app.services.automation_service import AutomationService

logger = logging.getLogger(__name__)

class BatchScanner:
    """
    Scanner de tâche de fond pour traiter les batches de messages
    
    Vérifie périodiquement les conversations dues et envoie les réponses
    """
    
    def __init__(self, scan_interval: float = 0.5):
        self.scan_interval = scan_interval  
        self.is_running = False
        self._task: asyncio.Task = None
        
    
    async def start(self):
        """Start the scanner in the background"""
        if self.is_running:
            logger.warning("Scanner already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._scan_loop())
        logger.info("Batch scanner started")
    
    async def stop(self):
        """Stop the scanner"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Batch scanner stopped")
    
    async def _scan_loop(self):
        """Main loop of the scanner"""
        while self.is_running:
            try:
                await self._process_due_conversations()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scanner: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def _process_due_conversations(self):
        """Process all due conversations"""
        try:
            due_conversations = await message_batcher.get_due_conversations()
            
            if due_conversations:
                logger.info(f"Processing {len(due_conversations)} due conversations")
                
                
                tasks = []
                for conv in due_conversations:
                    task = asyncio.create_task(
                        self._process_single_conversation(conv_info=conv)
                    )
                    tasks.append(task)
                
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
        except Exception as e:
            logger.error(f"Error processing due conversations: {e}")
    
    async def _process_single_conversation(self, conv_info: Dict[str, Any]):
        """
        Process a single conversation
        """
        platform = conv_info["platform"]
        account_id = conv_info["account_id"]
        contact_id = conv_info["contact_id"]
        conversation_key = conv_info["conversation_key"]
        conversation_id = conv_info["conversation_id"]
        
        try:
            
            batch_result = await message_batcher.process_batch_for_conversation(
                platform, account_id, contact_id, conversation_key, conversation_id
            )
            
            if not batch_result:
                logger.info(f"No batch result for {platform}:{account_id}:{contact_id}")
                await message_batcher.delete_conversation_cache(platform, account_id, contact_id)
                return
            
            if not isinstance(batch_result, dict) or "messages" not in batch_result or "context" not in batch_result:
                logger.warning(f"Invalid batch result structure for {platform}:{account_id}:{contact_id}: {batch_result}")
                return
            
            messages = batch_result["messages"]
            context = batch_result["context"]
            message_ids = batch_result["message_ids"]
            logger.info("=" * 60)
            logger.info(f"🔄 PROCESSING BATCH - {platform}:{account_id}:{contact_id}")
            logger.info("=" * 60)
            logger.info(f"🔑 Message IDs: {message_ids}")
            if isinstance(messages, dict):
                logger.info(f"📊 Messages in batch: 1 (concatenated)")
                logger.info(f"📄 Concatenated content length: {len(messages.get('message_data', {}).get('content', ''))} characters")
            else:
                logger.info(f"📊 Messages in batch: {len(messages)}")
            logger.info(f"📚 Context messages: {len(context)}")
            logger.info(f"🔑 Conversation ID: {conversation_id}")
            logger.info("-" * 60)
            
           
            if isinstance(messages, dict):
                content = messages.get("message_data", {}).get("content", "")
                direction = messages.get("message_data", {}).get("role", "user")
                logger.info(f"💬 Batch Message (concatenated) ({direction}): {content[:200]}{'...' if len(content) > 200 else ''}")

            if context:
                logger.info(f"📚 Context preview (last 3 messages):")
                for i, ctx in enumerate(context[-3:]):
                    content = ctx.get("message_data", {}).get("content", "")
                    direction = ctx.get("message_data", {}).get("direction", "unknown")
                    logger.info(f"   [{i+1}] ({direction}): {content[:80]}{'...' if len(content) > 80 else ''}")
            
            logger.info("-" * 60)
            
            user_credentials = await get_user_credentials_by_platform_account(platform, account_id)
            if not user_credentials:
                logger.error(f"Credentials not found for {platform}:{account_id}")
                return
            
           
            user_id = user_credentials.get("user_id")
            
            if conversation_id and user_id:
                from app.db.session import get_db
                automation_service = AutomationService(get_db())
                
                
                automation_check = await automation_service.should_auto_reply(
                    user_id=user_id
                )
                
                if not automation_check["should_reply"]:
                    logger.info(
                        f"Auto-response blocked for {platform}:{account_id}:{contact_id} - "
                        f"Reason: {automation_check['reason']}"
                    )
                    return
                else:
                    logger.info(
                        f"Auto-response allowed for {platform}:{account_id}:{contact_id} - "
                        f"Rules matched: {automation_check['reason']}"
                    )
            
             # Envoyer l'indicateur de frappe et marquer comme lu (en un seul appel)
            if message_ids:
                await send_typing_indicator(platform, user_credentials, contact_id, message_ids[-1])
                logger.info(f"📝 Typing indicator + read receipt sent for {platform}:{account_id}:{contact_id}")
            
            response = await generate_smart_response(messages, context, platform, automation_check["ai_settings"])
            response_content = response.get("response_content", "")
            prompt_tokens = response.get("prompt_tokens", 0)
            completion_tokens = response.get("completion_tokens", 0)
            model = response.get("model", "")
        
            # try:
            #     raw_group_id = await add_message_to_conversation_message_groups(
            #         conversation_id=conversation_id, 
            #         message=messages, 
            #         model=model, 
            #         user_id=user_id, 
            #         message_count=len(message_ids), 
            #         token_count=prompt_tokens, 
            #         message_ids=message_ids
            #     )                
            #     if not raw_group_id:
            #         logger.error(f"Failed to create message group for conversation {conversation_id}")
            #         return
            # except Exception as e:
            #     logger.error(f"Error adding message to conversation message groups: {e}")
            #     return
            
           
            if not response_content:
                logger.warning(f"❌ No response generated for {platform}:{account_id}:{contact_id}")
                logger.info("=" * 60)
                return
            
            logger.info(f"✅ Response generated successfully for {platform}:{account_id}:{contact_id}")
            logger.info("=" * 60)
            
            response_sent = await send_response(platform, user_credentials, contact_id, response_content)
            
            if response_sent:
                
                await message_batcher.add_response_to_history(
                    platform, account_id, contact_id,
                    {
                        "role": "assistant",
                        "content": response_content,
                    },
                    conversation_id
                )
                
                message_assistant_group_id = await save_response_to_db(
                    conversation_id, response_content, user_credentials.get("user_id")
                )
               
                response_message = {
                    "role": "assistant",
                    "content": response_content
                }
                # await add_message_to_conversation_message_groups(
                #     conversation_id=conversation_id, 
                #     message=response_message, 
                #     model=model, 
                #     user_id=user_id, 
                #     message_count=1, 
                #     token_count=completion_tokens, 
                #     message_ids=[message_assistant_group_id] if message_assistant_group_id else []
                # )
                
                logger.info(f"Response sent for {platform}:{account_id}:{contact_id}")
            
        except Exception as e:
            logger.error(f"Error processing {platform}:{account_id}:{contact_id}: {e}")
    

batch_scanner = BatchScanner()
