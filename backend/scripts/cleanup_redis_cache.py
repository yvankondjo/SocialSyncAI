#!/usr/bin/env python3
"""
Script pour nettoyer le cache Redis et éviter les doublons
"""
import asyncio
import redis.asyncio as redis
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def cleanup_redis_cache():
    """Nettoyer le cache Redis des conversations"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    async with redis.from_url(redis_url, decode_responses=True) as redis_client:
        # Supprimer toutes les clés de conversations
        pattern = "conv:*"
        keys = await redis_client.keys(pattern)
        
        if keys:
            logger.info(f"Suppression de {len(keys)} clés de conversation")
            await redis_client.delete(*keys)
            logger.info("Cache nettoyé avec succès")
        else:
            logger.info("Aucune clé de conversation trouvée")
        
        # Supprimer les deadlines
        deadlines_removed = await redis_client.delete("conv:deadlines")
        if deadlines_removed:
            logger.info("Deadlines supprimées")

if __name__ == "__main__":
    asyncio.run(cleanup_redis_cache())
