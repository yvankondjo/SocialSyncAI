#!/usr/bin/env python3
"""
Test manuel pour simuler un message entrant et tester le typing indicator
"""
import asyncio
import sys
import os
sys.path.append('/workspace/backend')

from app.services.response_manager import process_incoming_message_for_user

async def test_typing_indicator():
    """Test du typing indicator avec un message simulé"""
    
    # Message simulé (comme reçu par WhatsApp)
    message = {
        "id": "wamid.test123",
        "type": "text",
        "from": "33765540003",
        "text": {
            "body": "Test message pour typing indicator"
        },
        "timestamp": "1758487055"
    }
    
    # User info simulé
    user_info = {
        "user_id": "b46a7229-2c29-4a88-ada1-c21a59f4eda1",
        "social_account_id": "test-account-id",
        "account_id": "683178638221369",
        "phone_number_id": "683178638221369",
        "access_token": "YOUR_ACCESS_TOKEN",  # Remplacez par votre vrai token
        "platform": "whatsapp"
    }
    
    print("🧪 Test du typing indicator...")
    print(f"📱 Message: {message['text']['body']}")
    print(f"👤 Contact: {message['from']}")
    print(f"🔑 Account: {user_info['account_id']}")
    
    try:
        await process_incoming_message_for_user(message, user_info)
        print("✅ Test terminé - vérifiez les logs pour voir le typing indicator")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    asyncio.run(test_typing_indicator())
