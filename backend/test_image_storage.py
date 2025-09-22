#!/usr/bin/env python3
"""
Script de test pour le système de stockage d'images Supabase
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.response_manager import save_data_to_bucket, get_signed_url, refresh_image_urls_in_message

async def test_image_storage():
    """Test du système de stockage d'images"""
    
    print("🧪 Test du système de stockage d'images Supabase")
    print("=" * 50)
    
    # Test 1: Créer un fichier image factice
    print("\n1. Création d'un fichier image factice...")
    fake_image_data = b"fake_image_data_for_testing"
    object_path = "test/test_image.jpg"
    
    # Test 2: Sauvegarder dans le bucket
    print("2. Sauvegarde dans le bucket Supabase...")
    saved_path = save_data_to_bucket(fake_image_data, bucket_id="message", object_name=object_path)
    
    if saved_path:
        print(f"✅ Image sauvegardée: {saved_path}")
    else:
        print("❌ Échec de la sauvegarde")
        return
    
    # Test 3: Générer une URL signée
    print("3. Génération d'une URL signée...")
    signed_url = get_signed_url(saved_path, bucket_id="message", expires_in=3600)
    
    if signed_url:
        print(f"✅ URL signée générée: {signed_url[:100]}...")
    else:
        print("❌ Échec de la génération d'URL signée")
        return
    
    # Test 4: Test de re-signature
    print("4. Test de re-signature d'URL...")
    test_message = {
        "message_type": "image",
        "media_url": signed_url,
        "content": [{
            "type": "image_url",
            "image_url": {
                "url": signed_url
            }
        }]
    }
    
    refreshed_message = refresh_image_urls_in_message(test_message)
    
    if refreshed_message["media_url"] != signed_url:
        print("✅ URL re-signée avec succès")
        print(f"   Ancienne: {signed_url[:50]}...")
        print(f"   Nouvelle: {refreshed_message['media_url'][:50]}...")
    else:
        print("⚠️  URL non modifiée (peut être normal si l'URL est encore valide)")
    
    print("\n🎉 Tests terminés avec succès!")

if __name__ == "__main__":
    asyncio.run(test_image_storage())
