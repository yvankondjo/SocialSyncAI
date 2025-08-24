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
)

logger = logging.getLogger(__name__)

class BatchScanner:
    """
    Scanner de tâche de fond pour traiter les batches de messages
    
    Vérifie périodiquement les conversations dues et envoie les réponses
    """
    
    def __init__(self, scan_interval: float = 0.5):
        self.scan_interval = scan_interval  # Vérifier toutes les 500ms
        self.is_running = False
        self._task: asyncio.Task = None
        
    
    async def start(self):
        """Démarrer le scanner en arrière-plan"""
        if self.is_running:
            logger.warning("Scanner déjà en cours d'exécution")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._scan_loop())
        logger.info("Scanner de batches démarré")
    
    async def stop(self):
        """Arrêter le scanner"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Scanner de batches arrêté")
    
    async def _scan_loop(self):
        """Boucle principale du scanner"""
        while self.is_running:
            try:
                await self._process_due_conversations()
                await asyncio.sleep(self.scan_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans le scanner: {e}")
                await asyncio.sleep(self.scan_interval)
    
    async def _process_due_conversations(self):
        """Traiter toutes les conversations dues"""
        try:
            due_conversations = await message_batcher.get_due_conversations()
            
            if due_conversations:
                logger.info(f"Traitement de {len(due_conversations)} conversations dues")
                
                # Traiter chaque conversation
                tasks = []
                for conv in due_conversations:
                    task = asyncio.create_task(
                        self._process_single_conversation(conv)
                    )
                    tasks.append(task)
                
                # Attendre que toutes les conversations soient traitées
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement des conversations dues: {e}")
    
    async def _process_single_conversation(self, conv_info: Dict[str, Any]):
        """
        Traiter une conversation individuelle
        """
        platform = conv_info["platform"]
        account_id = conv_info["account_id"]
        contact_id = conv_info["contact_id"]
        
        try:
            # 1. Traiter le batch pour cette conversation
            batch_result = await message_batcher.process_batch_for_conversation(
                platform, account_id, contact_id
            )
            
            if not batch_result:
                # Déjà traité ou plus de messages
                return
            
            messages = batch_result["messages"]
            context = batch_result["context"]
            
            logger.info(f"Traitement batch {platform}:{account_id}:{contact_id} - {len(messages)} messages")
            
            # 2. Analyser les messages et générer une réponse intelligente
            response_content = await generate_smart_response(messages, context, platform)
            
            if not response_content:
                logger.info(f"Aucune réponse générée pour {platform}:{account_id}:{contact_id}")
                return
            
            # 3. Récupérer les credentials utilisateur
            user_credentials = await get_user_credentials_by_platform_account(platform, account_id)
            if not user_credentials:
                logger.error(f"Credentials non trouvés pour {platform}:{account_id}")
                return
            
            # 4. Envoyer la réponse via l'API appropriée
            response_sent = await send_response(platform, user_credentials, contact_id, response_content)
            
            if response_sent:
                # 5. Ajouter la réponse à l'historique Redis
                await message_batcher.add_response_to_history(
                    platform, account_id, contact_id, {
                        "content": response_content,
                        "message_type": "text",
                        "direction": "outbound",
                        "sent_at": datetime.now().isoformat()
                    }
                )
                
                # 6. Sauvegarder la réponse en BDD (avec fallback conversation_id)
                conversation_id = batch_result.get("conversation_id")
                if not conversation_id:
                    # fallback: retrouver/créer
                    from app.services.response_manager import get_or_create_conversation
                    conversation_id = await get_or_create_conversation(
                        social_account_id=user_credentials.get("id") or user_credentials.get("social_account_id"),
                        customer_identifier=contact_id,
                        customer_name=None
                    )
                await save_response_to_db(
                    conversation_id, response_content, user_credentials.get("user_id")
                )
                
                logger.info(f"Réponse envoyée pour {platform}:{account_id}:{contact_id}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {platform}:{account_id}:{contact_id}: {e}")
    

# Instance globale
batch_scanner = BatchScanner()
