#!/usr/bin/env python3
"""
Exemple d'utilisation du processeur OpenRouter
"""
import asyncio
from app.services.openrouter_message_processor import openrouter_processor

async def example_usage():
    """Exemple d'utilisation du processeur OpenRouter"""
    
    print("=== EXEMPLE D'UTILISATION OPENROUTER ===\n")
    
    # Simuler des messages entrants
    messages = [
        {
            "id": "msg_001",
            "content": "Bonjour, comment allez-vous ?",
            "type": "text"
        },
        {
            "id": "msg_002", 
            "content": "J'ai une question sur votre service",
            "type": "text"
        },
        {
            "id": "msg_003",
            "content": "Pouvez-vous m'aider ?",
            "type": "text"
        }
    ]
    
    conversation_id = "conv_123"
    user_id = "user_456"
    platform = "whatsapp"
    account_id = "683178638221369"
    contact_id = "33765540003"
    
    print("1. Traitement des messages entrants...")
    
    for i, message_data in enumerate(messages):
        print(f"   Message {i+1}: {message_data['content']}")
        
        result = await openrouter_processor.process_incoming_message(
            platform=platform,
            account_id=account_id,
            contact_id=contact_id,
            message_data=message_data,
            conversation_id=conversation_id,
            user_id=user_id,
            ai_model="gpt-4"
        )
        
        print(f"   → Groupe {'mis à jour' if result['group_updated'] else 'créé'}: {result['group_id']}")
        print(f"   → Messages OpenRouter: {len(result['openrouter_messages'])}")
    
    print("\n2. Récupération du groupe final...")
    
    # Récupérer le groupe actif
    active_groups = await openrouter_processor.get_active_groups(user_id, conversation_id)
    
    if active_groups:
        group = active_groups[0]
        print(f"   Groupe ID: {group['id']}")
        print(f"   Modèle: {group['model']}")
        print(f"   Messages: {len(group['messages'])}")
        print(f"   Contenu:")
        
        for i, msg in enumerate(group['messages']):
            print(f"     [{i+1}] {msg['role']}: {msg['content']}")
    
    print("\n3. Format OpenRouter pour l'API...")
    
    if active_groups:
        openrouter_format = await openrouter_processor.get_group_for_openrouter(active_groups[0]['id'])
        print(f"   Format API:")
        print(f"   {openrouter_format}")
    
    print("\n4. Ajout d'une réponse de l'assistant...")
    
    if active_groups:
        response_result = await openrouter_processor.add_assistant_response(
            group_id=active_groups[0]['id'],
            response_content="Bonjour ! Je vais bien, merci. Comment puis-je vous aider avec votre question sur notre service ?",
            ai_model="gpt-4"
        )
        
        print(f"   Réponse ajoutée: {response_result['success']}")
        print(f"   Messages totaux: {len(response_result['messages'])}")
    
    print("\n5. Finalisation du groupe...")
    
    # Simuler la finalisation (normalement fait par un cron job)
    await openrouter_processor.finalize_groups()
    print("   Groupes expirés finalisés")
    
    print("\n=== EXEMPLE TERMINÉ ===")

if __name__ == "__main__":
    asyncio.run(example_usage())



