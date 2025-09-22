#!/usr/bin/env python3
"""
Script pour analyser les groupes de messages avec un delta de 15 secondes
"""
import asyncio
import os
from datetime import datetime, timedelta
from app.db.session import get_db

async def analyze_message_groups():
    """Analyser les groupes de messages avec un delta de 15 secondes"""
    
    db = get_db()
    
    # Requête SQL pour grouper les messages par conversation et par fenêtre de 15 secondes
    query = """
    WITH message_groups AS (
        SELECT 
            cm.id,
            cm.content,
            cm.direction,
            cm.created_at,
            cm.external_message_id,
            c.id as conversation_id,
            c.customer_identifier,
            sa.account_id,
            sa.platform,
            -- Créer des groupes de 15 secondes en arrondissant les timestamps
            DATE_TRUNC('second', cm.created_at) + 
            INTERVAL '15 seconds' * FLOOR(
                EXTRACT(EPOCH FROM (cm.created_at - DATE_TRUNC('minute', cm.created_at))) / 15
            ) as time_group
        FROM conversation_messages cm
        INNER JOIN conversations c ON cm.conversation_id = c.id
        INNER JOIN social_accounts sa ON c.social_account_id = sa.id
        WHERE cm.direction = 'inbound'
        ORDER BY c.id, cm.created_at
    ),
    grouped_messages AS (
        SELECT 
            conversation_id,
            customer_identifier,
            account_id,
            platform,
            time_group,
            COUNT(*) as message_count,
            STRING_AGG(content, ' | ') as concatenated_content,
            MIN(created_at) as first_message_time,
            MAX(created_at) as last_message_time,
            ARRAY_AGG(external_message_id) as message_ids
        FROM message_groups
        GROUP BY conversation_id, customer_identifier, account_id, platform, time_group
        HAVING COUNT(*) > 1  -- Seulement les groupes avec plus d'un message
    )
    SELECT 
        conversation_id,
        customer_identifier,
        account_id,
        platform,
        time_group,
        message_count,
        concatenated_content,
        first_message_time,
        last_message_time,
        EXTRACT(EPOCH FROM (last_message_time - first_message_time)) as duration_seconds,
        message_ids
    FROM grouped_messages
    ORDER BY time_group DESC, conversation_id;
    """
    
    try:
        result = db.rpc('execute_sql', {'sql_query': query}).execute()
        
        if result.data:
            print("=== GROUPES DE MESSAGES DÉTECTÉS ===")
            print(f"Nombre de groupes trouvés: {len(result.data)}")
            print()
            
            for group in result.data:
                print(f"📱 Conversation: {group['conversation_id']}")
                print(f"   👤 Client: {group['customer_identifier']}")
                print(f"   📞 Compte: {group['account_id']} ({group['platform']})")
                print(f"   ⏰ Groupe temporel: {group['time_group']}")
                print(f"   📊 Messages: {group['message_count']}")
                print(f"   ⏱️  Durée: {group['duration_seconds']:.1f}s")
                print(f"   📝 Contenu: {group['concatenated_content'][:100]}...")
                print(f"   🆔 IDs: {group['message_ids']}")
                print("-" * 60)
        else:
            print("Aucun groupe de messages détecté")
            
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête: {e}")
        
        # Requête alternative plus simple si la fonction RPC n'existe pas
        print("\n=== REQUÊTE ALTERNATIVE ===")
        alternative_query = """
        SELECT 
            cm.id,
            cm.content,
            cm.direction,
            cm.created_at,
            cm.external_message_id,
            c.id as conversation_id,
            c.customer_identifier,
            sa.account_id,
            sa.platform
        FROM conversation_messages cm
        INNER JOIN conversations c ON cm.conversation_id = c.id
        INNER JOIN social_accounts sa ON c.social_account_id = sa.id
        WHERE cm.direction = 'inbound'
        ORDER BY c.id, cm.created_at
        LIMIT 20;
        """
        
        try:
            result = db.table("conversation_messages").select(
                "id, content, direction, created_at, external_message_id, "
                "conversations!inner(id, customer_identifier, "
                "social_accounts!inner(id, platform, account_id))"
            ).eq("direction", "inbound").order("created_at", desc=True).limit(20).execute()
            
            if result.data:
                print("Derniers 20 messages entrants:")
                for msg in result.data:
                    print(f"  {msg['created_at']} - {msg['content'][:50]}...")
            else:
                print("Aucun message trouvé")
                
        except Exception as e2:
            print(f"Erreur avec la requête alternative: {e2}")

if __name__ == "__main__":
    asyncio.run(analyze_message_groups())





