import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class SimpleBatcher:
    """
    Version tutorial du message batcher
    Vous allez compléter chaque méthode étape par étape
    """
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.batch_window_seconds = 30
        
    async def get_redis(self) -> redis.Redis:
        """
        TODO 1: Créer une connexion Redis
        
        Indice: redis.from_url()
        """
        return redis.from_url(self.redis_url)
    
    def _make_conversation_key(self, platform: str, account_id: str, contact_id: str) -> str:
        """
        TODO 2: Créer la clé de base pour une conversation
        
        Format: conv:platform:account_id:contact_id
        Exemple: conv:whatsapp:123456:789012
        """
        # Votre code ici 
        return f"conv:{platform}:{account_id}:{contact_id}"

    async def add_message_to_batch(self, platform: str, account_id: str, contact_id: str, message: dict):
        """
        TODO 3: Ajouter un message au batch
        
        Étapes :
        1. Créer la clé de conversation
        2. Vérifier si deadline existe déjà
        3. Si non, créer deadline = maintenant + 30s
        4. Ajouter message à la liste Redis
        5. Ajouter à l'agenda global si nouvelle conversation
        """
        redis_client = await self.get_redis()
        base_key = self._make_conversation_key(platform, account_id, contact_id)
        
        # Votre code ici :
        deadline = await redis_client.get(f"{base_key}:deadline")

        if not deadline:
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
                    {f"{base_key}": deadline_timestamp}
                )
                
                logger.info(f"⏰ Timer 30s démarré pour {base_key}, deadline: {deadline}")
        else:
            # Messages suivants → deadline INCHANGÉE
            existing_deadline_dt = datetime.fromtimestamp(int(deadline))
            logger.info(f"📝 Message ajouté au batch {base_key}, deadline inchangée: {existing_deadline_dt}")
            # Pas de ZADD car déjà dans l'agenda
            
            
        await redis_client.close()
    
    async def get_due_conversations(self) -> List[Dict]:
        """
        TODO 4: Récupérer les conversations dont la deadline est échue
        
        Indice: ZRANGEBYSCORE avec score <= maintenant
        """
        redis_client = await self.get_redis()
        now_timestamp = int(datetime.now().timestamp())
        
        # Votre code ici :
        # Utiliser ZRANGEBYSCORE sur conv:deadlines
        
        await redis_client.close()
        return []
    
    async def process_conversation_batch(self, platform: str, account_id: str, contact_id: str):
        """
        TODO 5: Traiter un batch de conversation
        
        Étapes :
        1. Récupérer tous les messages de la liste
        2. Vider la liste
        3. Supprimer de l'agenda global
        4. Générer une réponse
        """
        redis_client = await self.get_redis()
        base_key = self._make_conversation_key(platform, account_id, contact_id)
        
        # Votre code ici :
        
        await redis_client.close()

# Test de votre implémentation
async def test_batcher():
    """
    Fonction de test pour valider votre code
    """
    batcher = SimpleBatcher()
    
    print("🧪 Test 1: Ajouter des messages")
    await batcher.add_message_to_batch("whatsapp", "123", "456", {"content": "yo", "timestamp": "now"})
    await batcher.add_message_to_batch("whatsapp", "123", "456", {"content": "salut", "timestamp": "now+5s"})
    
    print("🧪 Test 2: Vérifier conversations dues (doit être vide)")
    due = await batcher.get_due_conversations()
    print(f"Conversations dues maintenant: {due}")
    
    print("🧪 Test 3: Attendre 2 secondes puis re-vérifier")
    await asyncio.sleep(2)
    due = await batcher.get_due_conversations()
    print(f"Conversations dues après 2s: {due}")
    
    print("🧪 Test 4: Traiter le batch")
    await batcher.process_conversation_batch("whatsapp", "123", "456")

if __name__ == "__main__":
    asyncio.run(test_batcher())
