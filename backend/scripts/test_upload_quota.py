#!/usr/bin/env python3
"""
Script de test pour vérifier l'enforcement du quota côté backend lors de l'upload.
"""

import os
import sys
import asyncio
import io
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_upload_with_quota():
    """Test l'upload avec vérification du quota."""
    
    client = TestClient(app)
    
    logger.info("🧪 Test 1: Upload fichier valide")
    
    # Créer un fichier PDF test
    test_file_content = b"%PDF-1.4\nTest content for upload\n" * 100  # ~3KB
    test_file = io.BytesIO(test_file_content)
    
    # Tenter l'upload (nécessite une authentification)
    # Note: Ce test nécessite un token JWT valide
    logger.info("⚠️ Ce test nécessite une authentification valide")
    logger.info("   Pour tester manuellement:")
    logger.info("   1. Obtenir un JWT token valide")
    logger.info("   2. Utiliser curl ou Postman")
    
    logger.info("\n📋 Exemple de test manuel avec curl:")
    logger.info("""
    # 1. Créer un fichier test
    echo "Test content" > test.txt
    
    # 2. Upload avec token
    curl -X POST "http://localhost:8000/api/knowledge_documents/upload" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
      -F "file=@test.txt"
    
    # 3. Vérifier la réponse (devrait inclure storage_usage)
    
    # 4. Créer un gros fichier pour tester le quota
    dd if=/dev/zero of=big_file.txt bs=1M count=50
    
    # 5. Tenter l'upload (devrait échouer si quota < 50MB)
    curl -X POST "http://localhost:8000/api/knowledge_documents/upload" \\
      -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
      -F "file=@big_file.txt"
    
    # Réponse attendue si quota dépassé:
    # {
    #   "detail": "Quota de stockage insuffisant. Disponible: X.XX MB, Requis: Y.YY MB"
    # }
    """)
    
    logger.info("\n✅ Points à vérifier:")
    logger.info("  1. Upload refusé si quota dépassé (code 400)")
    logger.info("  2. Message d'erreur explicite avec détails du quota")
    logger.info("  3. Pas d'insertion dans la DB si quota dépassé")
    logger.info("  4. storage_used_mb non incrémenté si upload échoue")
    logger.info("  5. Upload réussi si quota suffisant")
    logger.info("  6. storage_used_mb correctement incrémenté après upload réussi")

if __name__ == "__main__":
    logger.info("🚀 Test de l'enforcement du quota côté backend")
    test_upload_with_quota()
    logger.info("\n✅ Guide de test créé avec succès")


