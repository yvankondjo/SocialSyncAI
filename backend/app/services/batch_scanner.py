import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage
from app.services.message_batcher import message_batcher
from app.services.response_manager import (
    get_user_credentials_by_platform_account,
    send_response,
    save_response_to_db,
    send_typing_indicator_and_mark_read,
    generate_smart_response,
)
from app.services.automation_service import AutomationService

logger = logging.getLogger(__name__)

class BatchScanner:
    """
    Scanner of background task to process the batches of messages

    Check periodically the due conversations and send the responses
    """

    def __init__(self, scan_interval: float = 0.5):
        self.scan_interval = scan_interval
        self.is_running = False
        self._task: asyncio.Task = None

        # 📊 Métriques de monitoring
        self.metrics = {
            'conversations_processed': 0,
            'conversations_failed': 0,
            'conversations_timed_out': 0,
            'responses_generated': 0,
            'errors_total': 0,
            'processing_times': [],
            'last_scan_timestamp': None,
            'total_scans': 0
        }
        
    
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
                # 📊 Tracker les scans
                self.metrics['total_scans'] += 1
                self.metrics['last_scan_timestamp'] = datetime.now().isoformat()

                await self._process_due_conversations()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scanner: {e}")
                self.metrics['errors_total'] += 1
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

        # ⏱️ Measure the processing time for the metrics
        start_time = asyncio.get_event_loop().time()

        try:
            async with asyncio.timeout(30):
                batch_result = await message_batcher.process_batch_for_conversation(
                    platform, account_id, contact_id, conversation_key, conversation_id
                )
            
            if not batch_result:
                logger.info(f"No batch result for {platform}:{account_id}:{contact_id}")
                await message_batcher.delete_conversation_cache(platform, account_id, contact_id)
                # 📊 Métriques
                self.metrics['conversations_failed'] += 1
                self.metrics['errors_total'] += 1
                return
            
            if not isinstance(batch_result, dict) or "messages" not in batch_result:
                logger.warning(f"Invalid batch result structure for {platform}:{account_id}:{contact_id}: {batch_result}")
                # 📊 Métriques
                self.metrics['conversations_failed'] += 1
                self.metrics['errors_total'] += 1
                return
            
            messages = batch_result["messages"]
            message_ids = batch_result["message_ids"]
            logger.info("=" * 60)
            logger.info(f"🔄 PROCESSING BATCH - {platform}:{account_id}:{contact_id}")
            logger.info("=" * 60)
            logger.info(f"🔑 Message IDs: {message_ids}")
            if isinstance(messages, dict) and "message_data" in messages:
                logger.info(f"📊 Messages in batch: 1 (concatenated)")
                message_data = messages.get("message_data", {})
                content = message_data.get("content", "")
                logger.info(f"📄 Concatenated content length: {len(content)} characters")
            else:
                logger.info(f"📊 Messages in batch: {len(messages) if isinstance(messages, list) else 1}")
                content = messages.get("content", "") if isinstance(messages, dict) else ""
                logger.info(f"📄 Content length: {len(content)} characters")
            
            logger.info(f"🔑 Conversation ID: {conversation_id}")
            logger.info("-" * 60)
            
            # Debug: Log the full structure
            logger.info(f"🔍 DEBUG - Full messages structure: {messages}")
            logger.info(f"🔍 DEBUG - content extracted: '{content}'")
            
            direction = "user"
            if isinstance(messages, dict) and "message_data" in messages:
                direction = messages.get("message_data", {}).get("role", "user")
            elif isinstance(messages, dict):
                direction = messages.get("role", "user")
                
            logger.info(f"💬 Batch Message (concatenated) ({direction}): {content[:200]}{'...' if len(content) > 200 else ''}")

            logger.info("-" * 60)
            
            user_credentials = await get_user_credentials_by_platform_account(platform, account_id)
            if not user_credentials:
                logger.error(f"Credentials not found for {platform}:{account_id}")
                return
            
           
            user_id = user_credentials.get("user_id")
            
            
            automation_service = AutomationService()
            automation_check = automation_service.should_auto_reply(
                user_id=user_id,
                conversation_id=conversation_id,
                context_type="chat"
            )
            ai_settings = automation_check.get("ai_settings", {})

            # Check if AI is enabled for conversations (DM/chat messages)
            ai_enabled_for_conversations = ai_settings.get("ai_enabled_for_conversations", True)

            if not ai_enabled_for_conversations:
                logger.info(
                    f"🔕 AI disabled for conversations (user_id={user_id}). "
                    f"Skipping AI processing for {platform}:{account_id}:{contact_id}"
                )
                # Message is saved in DB but no AI response is generated
                return

            if conversation_id and user_id:
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
            else:
                logger.info(f"Processing without conversation_id or user_id for {platform}:{account_id}:{contact_id}")

        
            if message_ids and message_ids[-1]:
                await send_typing_indicator_and_mark_read(platform, user_credentials, contact_id, message_ids[-1])
                logger.info(f"📝 Typing indicator + read receipt sent for {platform}:{account_id}:{contact_id}")
            else:
                logger.warning(f"No valid message ID found for typing indicator: {message_ids}")

            content_message = self._format_messages(messages)
            logger.info(f"🔍 DEBUG - About to call generate_smart_response with content: {content_message}")
            logger.info(f"🔍 DEBUG - Content type: {type(content_message)}")
            logger.info(f"🔍 DEBUG - Content content: '{content_message[0].content if content_message else 'No content'}'")

            try:
                response_result = await generate_smart_response(content_message, user_id, ai_settings, conversation_id)
            except Exception as e:
                logger.error(f"🔍 DEBUG - Exception in generate_smart_response: {e}")
                logger.error(f"🔍 DEBUG - Exception type: {type(e)}")
                import traceback
                logger.error(f"🔍 DEBUG - Traceback: {traceback.format_exc()}")
                raise e

            # Vérifier si la réponse est un succès ou une erreur
            if isinstance(response_result, dict):
                if 'error' in response_result:
                    # Erreur dans l'agent RAG
                    logger.error(f"❌ Error in RAG agent: {response_result['error']}")
                    logger.info("=" * 60)
                    # 📊 Métriques
                    self.metrics['conversations_failed'] += 1
                    self.metrics['errors_total'] += 1
                    return
                elif 'messages' in response_result:
                    # Réponse réussie - extraire le contenu du dernier message AI
                    messages = response_result['messages']
                    ai_message = None
                    for msg in reversed(messages):
                        if hasattr(msg, 'type') and msg.type == 'ai':
                            ai_message = msg
                            break
                        elif msg.__class__.__name__ == 'AIMessage':
                            ai_message = msg
                            break

                    if ai_message and hasattr(ai_message, 'content'):
                        # Essayer de parser le JSON dans le contenu
                        try:
                            import json
                            content_data = json.loads(ai_message.content)
                            response_content = content_data.get("response", ai_message.content)
                            response_confidence = content_data.get("confidence", 1.0)
                        except (json.JSONDecodeError, KeyError):
                            response_content = ai_message.content
                            response_confidence = 1.0
                    else:
                        logger.warning(f"❌ No AI message found in response for {platform}:{account_id}:{contact_id}")
                        logger.info("=" * 60)
                        # 📊 Métriques
                        self.metrics['conversations_failed'] += 1
                        self.metrics['errors_total'] += 1
                        return
                else:
                    logger.error(f"❌ Unexpected dict response format: {response_result}")
                    logger.info("=" * 60)
                    # 📊 Métriques
                    self.metrics['conversations_failed'] += 1
                    self.metrics['errors_total'] += 1
                    return
            elif not response_result:
                logger.warning(f"❌ No response generated for {platform}:{account_id}:{contact_id}")
                logger.info("=" * 60)
                # 📊 Métriques
                self.metrics['conversations_failed'] += 1
                self.metrics['errors_total'] += 1
                return
            else:
                # Réponse sous forme de chaîne (ancien format)
                response_content = response_result
                response_confidence = None

            if not response_content:
                logger.warning(f"❌ Empty response generated for {platform}:{account_id}:{contact_id}")
                return
            logger.info(f"✅ Response generated successfully for {platform}:{account_id}:{contact_id}")
            logger.info(f"🔑 Response content: {response_content}")
            logger.info("=" * 60)

            response_sent = await send_response(platform, user_credentials, contact_id, response_content)

            if response_sent:
                # Save the response to the DB
                message_assistant_group_id = save_response_to_db(
                    conversation_id,
                    response_content,
                    user_credentials.get("user_id"),
                    confidence=response_confidence,
                )

                logger.info(f"Response sent for {platform}:{account_id}:{contact_id}")

                # 📊 Métriques de succès
                end_time = asyncio.get_event_loop().time()
                processing_time = end_time - start_time
                self.metrics['conversations_processed'] += 1
                self.metrics['responses_generated'] += 1
                self.metrics['processing_times'].append(processing_time)
                # Garder seulement les 100 derniers temps
                if len(self.metrics['processing_times']) > 100:
                    self.metrics['processing_times'] = self.metrics['processing_times'][-100:]
            else:
                # Réponse générée mais pas envoyée
                logger.error(f"❌ Failed to send response for {platform}:{account_id}:{contact_id}")
                # 📊 Métriques d'échec
                end_time = asyncio.get_event_loop().time()
                processing_time = end_time - start_time
                self.metrics['conversations_failed'] += 1
                self.metrics['errors_total'] += 1
                self.metrics['processing_times'].append(processing_time)
                if len(self.metrics['processing_times']) > 100:
                    self.metrics['processing_times'] = self.metrics['processing_times'][-100:]

        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout (30s) processing {platform}:{account_id}:{contact_id}")
            await message_batcher.delete_conversation_cache(platform, account_id, contact_id)
            # 📊 Métriques
            self.metrics['conversations_timed_out'] += 1
            self.metrics['errors_total'] += 1
        except Exception as e:
            logger.error(f"Error processing {platform}:{account_id}:{contact_id}: {e}")
            # 📊 Métriques
            self.metrics['conversations_failed'] += 1
            self.metrics['errors_total'] += 1
    
    def _format_messages(self, messages: Dict[str, Any]) -> List[HumanMessage]:
        """
        Format the messages for the agent
        """
        logger.info(f"🔍 DEBUG _format_messages - Input messages: {messages}")
        
        # La structure peut être soit:
        # 1. {"message_data": {"content": "...", "role": "user"}} (ancienne structure texte)
        # 2. {"message_data": {"content": [{"type": "text"}, {"type": "image_url"}], "role": "user"}} (structure multimédia)
        # 3. {"content": "...", "role": "user"} (nouvelle structure)
        
        if isinstance(messages, dict) and "message_data" in messages:
            # Ancienne structure
            message_data = messages.get("message_data", {})
            content = message_data.get("content", "")
            logger.info(f"🔍 DEBUG _format_messages - content from message_data: '{content}'")
        else:
            # Nouvelle structure ou structure directe
            content = messages.get("content", "")
            logger.info(f"🔍 DEBUG _format_messages - content from messages: '{content}'")
        
        # Nettoyer le contenu uniquement si c'est une chaîne
        if isinstance(content, str):
            content = content.strip()
            logger.info(f"🔍 DEBUG _format_messages - Final content (cleaned): '{content}'")
        else:
            logger.info(f"🔍 DEBUG _format_messages - Final content (complex): {type(content)}")
        
        return [HumanMessage(content=content)]

    # 📊 Méthodes de monitoring
    def get_metrics(self) -> Dict[str, Any]:
        """Récupérer les métriques de performance"""
        metrics = self.metrics.copy()
        if metrics['processing_times']:
            metrics['avg_processing_time'] = sum(metrics['processing_times']) / len(metrics['processing_times'])
            metrics['max_processing_time'] = max(metrics['processing_times'])
            metrics['min_processing_time'] = min(metrics['processing_times'])
        else:
            metrics['avg_processing_time'] = 0
            metrics['max_processing_time'] = 0
            metrics['min_processing_time'] = 0
        return metrics

    def log_performance_metrics(self):
        """Logger les métriques de performance"""
        metrics = self.get_metrics()
        logger.info(f"  - Conversations traitées: {metrics['conversations_processed']}")
        logger.info(f"  - Échecs: {metrics['conversations_failed']}")
        logger.info(f"  - Timeouts: {metrics['conversations_timed_out']}")
        logger.info(f"  - Réponses générées: {metrics['responses_generated']}")
        logger.info(f"  - Erreurs totales: {metrics['errors_total']}")
        logger.info(f"  - Scans totaux: {metrics['total_scans']}")

        if metrics['processing_times']:
            logger.info(f"  - Temps moyen de traitement: {metrics['avg_processing_time']:.2f}s")
            logger.info(f"  - Temps max: {metrics['max_processing_time']:.2f}s")
            logger.info(f"  - Temps min: {metrics['min_processing_time']:.2f}s")

        # Calculer les taux de succès
        total_processed = metrics['conversations_processed'] + metrics['conversations_failed']
        if total_processed > 0:
            success_rate = (metrics['conversations_processed'] / total_processed) * 100
            logger.info(f"  - Taux de succès: {success_rate:.1f}%")

    def get_health_status(self) -> Dict[str, Any]:
        """Récupérer le statut de santé du scanner"""
        metrics = self.get_metrics()
        return {
            'is_running': self.is_running,
            'last_scan': metrics['last_scan_timestamp'],
            'total_scans': metrics['total_scans'],
            'conversations_processed': metrics['conversations_processed'],
            'errors_total': metrics['errors_total'],
            'success_rate': (metrics['conversations_processed'] / (metrics['conversations_processed'] + metrics['conversations_failed']) * 100) if (metrics['conversations_processed'] + metrics['conversations_failed']) > 0 else 0,
            'avg_response_time': metrics['avg_processing_time']
        }

# Instance globale du scanner
batch_scanner = BatchScanner()